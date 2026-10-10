from modules.source_menu import SourceMenu
from modules.news_menu import NewsMenu
from modules.crawler_menu import CrawlerMenu


class MainMenu:
    def __init__(self, source_repo, category_repo, news_repo):
        self.source_menu = SourceMenu(source_repo, category_repo)
        self.news_menu = NewsMenu(news_repo, source_repo)
        self.crawler_menu = CrawlerMenu(source_repo, news_repo)

    def run(self):
        try:
            while True:
                print("\n/=== CHƯƠNG TRÌNH TỔNG HỢP TIN TỨC ĐA NGUỒN ===/")
                print("1. Quản lý nguồn tin (Source Management)")
                print("2. Quản lý tin tức (News Article Management)")
                print("3. Chạy Crawler (Crawl Data)")
                print("0. Thoát chương trình")
                choice = input("Chọn: ").strip()
                if choice == "1":
                    self.source_menu.run()
                elif choice == "2":
                    self.news_menu.run()
                elif choice == "3":
                    self.crawler_menu.run()
                elif choice == "0":
                    print("Tạm biệt!")
                    break
                else:
                    print("Lựa chọn không hợp lệ.")
        except KeyboardInterrupt:
            print("\nĐã thoát chương trình.")