from config import GEMINI_CONFIG, REWRITE_BATCH_SIZE, REWRITE_DELAY_SECONDS, REWRITE_MAX_ATTEMPTS
from modules.utils import print_table
from services.gemini_client import GeminiClient
from services.rewrite_service import RewriteService

class RewriteMenu:
    def __init__(self, rewrite_repo):
        self.rewrite_repo = rewrite_repo

    def run(self):
        while True:
            print("\n/--- BOT 3: AI VIẾT LẠI BÀI ĐÃ CÀO ---/")
            print("3.3.1. Chạy bot 3 (AI viết lại các bài chưa được viết lại)")
            print("3.3.2. Xem thống kê bot 3")
            print("0. Quay lại menu Chạy Crawler")
            choice = input("Chọn: ").strip()
            if choice == "1":
                self.run_bot()
            elif choice == "2":
                self.show_stats()
            elif choice == "0":
                break
            else:
                print("Lựa chọn không hợp lệ.")

    def run_bot(self):
        if not GEMINI_CONFIG["api_key"] or not GEMINI_CONFIG["model"]:
            print("Chưa cấu hình AI. Mở file .env trong thư mục dự án, điền GEMINI_API_KEY và GEMINI_MODEL, "
                  "rồi mở lại chương trình.")
            print("(Chạy check_gemini.py để tìm model còn dùng được.)")
            return
        waiting = self.rewrite_repo.count_waiting(REWRITE_MAX_ATTEMPTS)
        print(f"Số bài đang chờ viết lại: {waiting} | Mô hình: {GEMINI_CONFIG['model']}")
        if waiting == 0:
            return
        raw = input(f"Số bài tối đa viết lại ở lượt này [Enter = {REWRITE_BATCH_SIZE}]: ").strip()
        try:
            limit = int(raw) if raw else REWRITE_BATCH_SIZE
        except ValueError:
            print("Phải nhập một số nguyên.")
            return
        if limit < 1:
            print("Số bài phải từ 1 trở lên.")
            return
        client = GeminiClient(GEMINI_CONFIG["api_key"], GEMINI_CONFIG["model"])
        service = RewriteService(self.rewrite_repo, client, REWRITE_DELAY_SECONDS, REWRITE_MAX_ATTEMPTS)
        try:
            service.run(limit)
        except KeyboardInterrupt:
            print("\nĐã dừng bot 3 (các bài đã xong vẫn được lưu).")

    def show_stats(self):
        stats = self.rewrite_repo.get_stats()
        done = stats.get("completed", {})
        failed = stats.get("failed", {})
        print(f"Đã viết lại xong : {done.get('so_bai', 0)} bài "
              f"(token vào {done.get('tong_input', 0)}, token ra {done.get('tong_output', 0)})")
        print(f"Bị lỗi           : {failed.get('so_bai', 0)} bài")
        print(f"Đang chờ viết lại: {self.rewrite_repo.count_waiting(REWRITE_MAX_ATTEMPTS)} bài")
        failures = self.rewrite_repo.get_failed(10)
        if failures:
            print("\nCác bài lỗi gần nhất:")
            print_table(["ID bài", "Số lần thử", "Lỗi"],
                        [(f.article_id, f.attempts, f.error_message or "") for f in failures],
                        [8, 12, 90])