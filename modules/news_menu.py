import math
from datetime import datetime

from modules.export_menu import ExportMenu
from modules.utils import read_int, print_table
from services.export_service import ExportService

PAGE_SIZE = 10


class NewsMenu:
    def __init__(self, news_repo, source_repo):
        self.news_repo = news_repo
        self.source_repo = source_repo
        self.export_menu = ExportMenu(ExportService(news_repo))

    def run(self):
        while True:
            print("\n--- QUẢN LÝ TIN TỨC ---")
            print("2.1. Xem danh sách tin tức (phân trang bằng < và >)")
            print("2.2. Tìm kiếm tin tức")
            print("2.3. Lọc tin tức theo Nguồn hoặc Ngày cào")
            print("2.4. Xem chi tiết một bài viết")
            print("2.5. Xóa tin tức")
            print("2.6. Xuất file (CSV/JSON)")
            print("0. Quay lại Menu chính")
            choice = input("Chọn: ").strip()
            if choice == "1":
                self.paginate()
            elif choice == "2":
                self.search()
            elif choice == "3":
                self.filter_news()
            elif choice == "4":
                self.show_detail()
            elif choice == "5":
                self.delete_news()
            elif choice == "6":
                self.export_menu.run()
            elif choice == "0":
                break
            else:
                print("Lựa chọn không hợp lệ.")

    def paginate(self, **filters):
        page = 1
        while True:
            total = self.news_repo.count(**filters)
            if total == 0:
                print("Không có bài viết phù hợp.")
                return
            total_pages = math.ceil(total / PAGE_SIZE)
            rows = self.news_repo.get_page((page - 1) * PAGE_SIZE, PAGE_SIZE, **filters)
            print_table(["ID", "Tiêu đề", "Nguồn", "Ngày cào"],
                        [(r["id"], r["title"] or "", r["source_name"], r["created_at"]) for r in rows],
                        [6, 60, 15, 22])
            print(f"Trang {page}/{total_pages} ({total} bài)")
            key = input("[<] trang trước | [>] trang sau | [0] thoát: ").strip()
            if key == ">" and page < total_pages:
                page += 1
            elif key == "<" and page > 1:
                page -= 1
            elif key == "0":
                return

    def search(self):
        keyword = input("Nhập từ khóa (tiêu đề hoặc nội dung): ").strip()
        if not keyword:
            print("Từ khóa không được để trống.")
            return
        self.paginate(keyword=keyword)

    def filter_news(self):
        print("1. Lọc theo Nguồn")
        print("2. Lọc theo Ngày cào")
        choice = input("Chọn: ").strip()
        if choice == "1":
            sources = self.source_repo.get_all()
            print_table(["ID", "Tên nguồn"], [(s.id, s.name) for s in sources], [6, 30])
            self.paginate(source_id=read_int("Nhập ID nguồn: "))
        elif choice == "2":
            date_text = input("Nhập ngày cào (YYYY-MM-DD): ").strip()
            try:
                datetime.strptime(date_text, "%Y-%m-%d")
            except ValueError:
                print("Sai định dạng ngày, ví dụ đúng: 2026-10-07")
                return
            self.paginate(crawl_date=date_text)
        else:
            print("Lựa chọn không hợp lệ.")

    def show_detail(self):
        detail = self.news_repo.get_detail(read_int("Nhập ID bài viết: "))
        if detail is None:
            print("Không tìm thấy bài viết.")
            return
        print(f"\nTiêu đề   : {detail['title']}")
        print(f"Tóm tắt   : {detail['summary']}")
        print(f"Nội dung  : {detail['content']}")
        print(f"Đường dẫn : {detail['url']}")
        print(f"Ngày đăng : {detail['source_published_at']}")

    def delete_news(self):
        print("1. Xóa một bài theo ID")
        print("2. Xóa các bài cũ hơn N ngày")
        choice = input("Chọn: ").strip()
        if choice == "1":
            article_id = read_int("Nhập ID bài cần xóa: ")
            if input("Xác nhận xóa? (y/n): ").strip().lower() == "y":
                result = self.news_repo.soft_delete(article_id)
                print("Đã xóa." if result > 0 else "Không tìm thấy bài hoặc xóa thất bại.")
        elif choice == "2":
            days = read_int("Xóa bài cũ hơn bao nhiêu ngày? ")
            if input(f"Xác nhận xóa bài cũ hơn {days} ngày? (y/n): ").strip().lower() == "y":
                result = self.news_repo.soft_delete_older_than(days)
                print(f"Đã xóa {max(result, 0)} bài.")
        else:
            print("Lựa chọn không hợp lệ.")