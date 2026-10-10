from config import DB_CONFIG
from database.mysql_handler import MySqlHandler
from repositories.source_repository import SourceRepository
from repositories.category_repository import CategoryRepository
from repositories.news_repository import NewsRepository
from modules.main_menu import MainMenu

if __name__ == "__main__":
    db = MySqlHandler(DB_CONFIG)
    MainMenu(SourceRepository(db), CategoryRepository(db), NewsRepository(db)).run()


# if __name__ == "__main__":
#     crawler_service: CrawlerService
#     # if else switch case
#     # Không ép biến vào thì không dùng print(f"")
#     print("Choose Source:")
#     print("1. VnExpress")
#     print("2. Mương 14")
#     print("3. Dân trí")
#     source_choice = 1
#     if(source_choice == 1):
#         crawler_service = VnexpressCrawlerService()
#     elif(source_choice == 2):
#         crawler_service = Muong14CrawlerService()
#     elif(source_choice == 3):
#         crawler_service = DantriCrawlerService()
#     # Trong trường hợp cần 1 giá trị default nếu người dùng không chọn các lựa chọn đã có sẵn
#     # (ở đây đang là "1", "2" hoặc "3")
#     else:
#         crawler_service = VnexpressCrawlerService()

#     crawler_service.crawl_fresh_link()
#     crawler_service.crawl_link_detail()


# #Diamond Thread - Main Thread
# if __name__ == "__main__":
#     #1. Khởi tạo DB
#     db_conn = init_database()

#     #Nơi điền URL
#     url = "https://vnexpress.net"

#     headers = {
#         'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
#     }
    
#     response = requests.get(url, headers=headers, timeout=10)
#     soup = BeautifulSoup (response.text, 'html.parser')
    
#     #2. Bắt đầu cào dữ liệu
#     title_tag = soup.select_one('h1.title_detail')
#     news_title = title_tag.text
#     print(news_title)
    
#     content_detail_tag = soup.select_one('articlearticle.fck_detail')
#     content_detail = content_detail_tag.text
#     print(content_detail)
    
#     #Lấy 1 thẻ div có class là fig_piture, bên trong lấy 1 thằng con là picture, trong picture lấy 1 img
#     image_tag= soup.select_one('div.fig_picture picture img')
#     image_url = image_tag ['data-src']