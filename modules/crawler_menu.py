import re
import threading
import time
from datetime import datetime, timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from modules.utils import read_int
from modules.rewrite_menu import RewriteMenu
from services.crawler_service import create_crawler
from repositories.rewrite_repository import RewriteRepository

DEFAULT_CRON = "*/30 * * * *"      # mỗi 30 phút (ví dụ của đề)
WARN_GAP_MINUTES = 10              # chu kỳ ngắn hơn mức này thì cảnh báo (không chặn)

# Các ngày trong tuần theo chuẩn crontab: 0 (hoặc 7) = Chủ Nhật, 1 = Thứ Hai, ..., 6 = Thứ Bảy
CRON_DAYS = ["sun", "mon", "tue", "wed", "thu", "fri", "sat"]

# APScheduler 3.x đánh số thứ lệch chuẩn crontab (0 = Thứ Hai)
# Đổi trường 'thứ' của crontab chuẩn sang tên viết tắt (mon, tue, ...) để lịch chạy đúng ngày.
def cron_weekday_to_names(field):
    if field.strip() == "*":
        return "*"

    def to_number(token):
        token = token.lower()
        if token in CRON_DAYS:
            return CRON_DAYS.index(token)
        if token.isdigit() and 0 <= int(token) <= 7:
            return int(token)
        raise ValueError(f"Giá trị thứ không hợp lệ: '{token}' (dùng 0-7 hoặc sun, mon, tue, wed, thu, fri, sat)")

    days = set()
    for part in field.split(","):
        match = re.fullmatch(r"(\*|[A-Za-z0-9]+)(?:-([A-Za-z0-9]+))?(?:/(\d+))?", part.strip())
        if not match:
            raise ValueError(f"Trường thứ không hợp lệ: '{part}'")
        first, last, step = match.groups()
        step = int(step) if step else 1
        if step < 1:
            raise ValueError("Bước nhảy phải từ 1 trở lên")
        start = 0 if first == "*" else to_number(first)
        if first == "*":
            end = 6
        elif last:
            end = to_number(last)
            if end == 0 and start > 0:      # 'fri-sun' hoặc '5-0' hiểu là đến hết Chủ Nhật
                end = 7
        else:
            end = 6 if match.group(3) else start
        if end < start:
            raise ValueError(f"Khoảng thứ không hợp lệ: '{part}'")
        days.update(d % 7 for d in range(start, end + 1, step))
    return ",".join(CRON_DAYS[d] for d in sorted(days))

# Biểu thức crontab 5 trường (phút giờ ngày tháng thứ) -> CronTrigger của APScheduler. Sai -> ValueError.
def build_trigger(expr):
    fields = expr.split()
    if len(fields) != 5:
        raise ValueError(f"Cần đúng 5 trường (phút giờ ngày tháng thứ), bạn nhập {len(fields)} trường")
    fields[4] = cron_weekday_to_names(fields[4])
    return CronTrigger.from_crontab(" ".join(fields))

# Các thời điểm chạy kế tiếp theo lịch (theo múi giờ của máy).
def next_runs(trigger, count=3):
    runs, previous, current = [], None, datetime.now(trigger.timezone)
    for _ in range(count):
        following = trigger.get_next_fire_time(previous, current)
        if following is None:
            break
        runs.append(following)
        previous = current = following
    return runs

class CrawlerMenu:
    def __init__(self, source_repo, news_repo):
        self.source_repo = source_repo
        self.news_repo = news_repo
        self.rewrite_menu = RewriteMenu(RewriteRepository(news_repo.db))

    def run(self):
        while True:
            print("\n/--- CHẠY CRAWLER ---/")
            print("3.1. Chạy ngay (tất cả nguồn đang Active hoặc một nguồn cụ thể)")
            print("3.2. Chạy tự động theo lịch crontab")
            print("3.3. Viết lại các bài đã cào (Google AI Studio/Gemini)")
            print("0. Quay lại Menu chính")
            choice = input("Chọn: ").strip()
            if choice == "1":
                self.run_once()
            elif choice == "2":
                self.run_scheduled()
            elif choice == "3":
                self.rewrite_menu.run()    
            elif choice == "0":
                break
            else:
                print("Lựa chọn không hợp lệ.")
    
    # Chọn nguồn
    # Hiện danh sách nguồn Active. 
    # Trả về 0 (tất cả) hoặc ID nguồn đã chọn; không hợp lệ -> None.
    def choose_source_id(self):
        sources = self.source_repo.get_active()
        if not sources:
            print("Không có nguồn nào đang Active.")
            return None
        print("0. Tất cả các nguồn đang Active")
        for s in sources:
            print(f"{s.id}. {s.name}")
        choice = read_int("Chọn: ")
        if choice != 0 and choice not in [s.id for s in sources]:
            print("Nguồn không tồn tại hoặc đang Inactive.")
            return None
        return choice

    # Đọc lại danh sách nguồn Active từ DB (mỗi lượt cào đều đọc lại).
    def get_target_sources(self, source_id):
        sources = self.source_repo.get_active()
        return sources if source_id == 0 else [s for s in sources if s.id == source_id]

    # Thực hiện 1 lượt cào:
    def crawl_sources(self, sources):
        for source in sources:
            crawler = create_crawler(source, self.news_repo)
            if crawler is None:
                print(f"[{source.name}] Chưa có file crawler cho domain '{source.domain}', bỏ qua.")
                continue
            crawler.crawl_fresh_link()
            crawler.crawl_link_detail()
    
    def run_once(self):
        source_id = self.choose_source_id()
        if source_id is None:
            return
        self.crawl_sources(self.get_target_sources(source_id))

    # Cào tự động theo lịch của CronTab
    def ask_cron_trigger(self):
        """Hỏi biểu thức crontab đến khi hợp lệ. Nhập 0 để hủy -> None."""
        print("Nhập biểu thức crontab: phút giờ ngày tháng thứ")
        print("  */30 * * * *        mỗi 30 phút")
        print("  0 8 * * *           8 giờ sáng hằng ngày")
        print("  */5 9-17 * * 1-5    mỗi 5 phút trong 9h-17h, Thứ Hai đến Thứ Sáu")
        while True:
            raw = input(f"Biểu thức crontab [Enter = {DEFAULT_CRON}, 0 = hủy]: ").strip()
            if raw == "0":
                return None
            try:
                return build_trigger(raw or DEFAULT_CRON)
            except ValueError as e:
                print(f"Biểu thức không hợp lệ: {e}")

    # Một lượt cào của lịch. 
    # Lượt trước chưa xong thì bỏ qua; lỗi bất kỳ chỉ in ra, không làm dừng lịch.
    def scheduled_job(self, source_id, state, trigger):
        if not state["lock"].acquire(blocking=False):
            print("\nLượt cào trước chưa xong, bỏ qua lượt này.")
            return
        try:
            state["count"] += 1
            print(f"\n=== Lượt cào #{state['count']} lúc {datetime.now():%d/%m/%Y %H:%M:%S} ===")
            try:
                self.crawl_sources(self.get_target_sources(source_id))
            except Exception as e:
                print(f"Lỗi ở lượt cào #{state['count']}: {e}")
            upcoming = next_runs(trigger, 1)
            if upcoming and not state["stopping"]:
                print(f"Lượt tiếp theo lúc {upcoming[0]:%d/%m %H:%M}. Nhấn Ctrl+C để dừng và quay lại menu.")
        finally:
            state["lock"].release()

    # Nếu đang có lượt cào chạy dở thì chờ đến khi xong (Ctrl+C lần nữa để bỏ qua).
    def wait_job_finished(self, state):
        if not state["lock"].locked():
            return
        print("Đang chờ lượt cào hiện tại hoàn tất (nhấn Ctrl+C lần nữa để bỏ qua)...")
        try:
            while state["lock"].locked():
                time.sleep(0.5)
        except KeyboardInterrupt:
            print("Lượt cào hiện tại vẫn chạy ngầm và sẽ tự kết thúc.")

    def run_scheduled(self):
        source_id = self.choose_source_id()
        if source_id is None:
            return
        trigger = self.ask_cron_trigger()
        if trigger is None:
            return
        runs = next_runs(trigger)
        print("Các lần chạy kế tiếp theo lịch: " + ", ".join(f"{r:%d/%m %H:%M}" for r in runs))
        if len(runs) >= 2 and runs[1] - runs[0] < timedelta(minutes=WARN_GAP_MINUTES):
            print(f"Lưu ý: lịch dưới {WARN_GAP_MINUTES} phút/lần dễ bị website chặn, nên dùng từ 30 phút trở lên.")
        run_now = input("Cào ngay một lượt trước khi chờ lịch? (y/n) [y]: ").strip().lower() != "n"

        state = {"count": 0, "lock": threading.Lock(), "stopping": False}
        scheduler = BackgroundScheduler()
        # max_instances > 1: để chính khóa (lock) trong scheduled_job quyết định bỏ qua lượt chồng
        # và in thông báo tiếng Việt, thay vì thông báo tiếng Anh của APScheduler
        scheduler.add_job(self.scheduled_job, trigger, args=[source_id, state, trigger],
                          max_instances=3, coalesce=True, misfire_grace_time=300)
        scheduler.start()
        print("Đã bật chạy tự động. Nhấn Ctrl+C để dừng và quay lại menu.")
        try:
            if run_now:
                self.scheduled_job(source_id, state, trigger)
            while True:
                time.sleep(1)               # vòng chờ ở luồng chính, Ctrl+C ngắt được cả trên Windows
        except KeyboardInterrupt:
            state["stopping"] = True
            print("\nĐang dừng chạy tự động...")
        finally:
            scheduler.shutdown(wait=False)
            self.wait_job_finished(state)
        print("Đã dừng chạy tự động, quay lại menu.")

        # sources = self.source_repo.get_active()
        # if not sources:
        #     print("Không có nguồn nào đang Active.")
        #     return
        # print("\n--- CHẠY CRAWLER ---")
        # print("0. Tất cả các nguồn đang Active")
        # for s in sources:
        #     print(f"{s.id}. {s.name}")
        # choice = read_int("Chọn: ")
        # if choice != 0:
        #     sources = [s for s in sources if s.id == choice]
        #     if not sources:
        #         print("Nguồn không tồn tại hoặc đang Inactive.")
        #         return
        # for source in sources:
        #     crawler = create_crawler(source, self.news_repo)
        #     if crawler is None:
        #         print(f"[{source.name}] Chưa có file crawler cho domain '{source.domain}', bỏ qua.")
        #         continue
        #     crawler.crawl_fresh_link()
        #     crawler.crawl_link_detail()