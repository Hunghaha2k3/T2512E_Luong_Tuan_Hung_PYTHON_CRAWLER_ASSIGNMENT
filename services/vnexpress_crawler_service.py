# from urllib.parse import urlparse  
from services.crawler_service import CrawlerService

# Nội dung tạm cho những bài có định dạng đặc biệt (Không có văn bản trong HTML, định dạng video...)
# Query DB: content LIKE '[Bài đặc biệt]%'
SPECIAL_CONTENT_NOTE = ("[Bài đặc biệt] Không có nội dung văn bản trong HTML "
                        "(video hoặc định dạng khác). Xem bài gốc tại đường dẫn.")

class VnexpressCrawlerService(CrawlerService):
    DOMAIN = "vnexpress.net"      

    LINK_SELECTOR = "article h3.title-news a"
    # TITLE_SELECTOR và CONTENT_SELECTOR là DANH SÁCH selector (không phải chuỗi).  
    # Thử lần lượt, selector đầu tiên có kết quả thì dùng.
    # Mục 1: bài thường | Mục 2: bài podcast (tiêu đề h1.title-news, nội dung là bản chép lời)    
    TITLE_SELECTOR = ["h1.title-detail", "h1.title-news"]                          
    SUMMARY_SELECTOR = "p.description"                        
    CONTENT_SELECTOR = ['article.fck_detail p.Normal:not([style*="text-align:right"])',
                        "div.tab-transcript p.Normal"]                        
    AUTHOR_SELECTOR = 'article.fck_detail p.Normal[style*="text-align:right"]'
    PUBLISHED_SELECTOR = 'meta[name="pubdate"]'

    # Hàm xử lý các bài đặc biệt (chỉ lưu metadata) trong lượt chạy này
    def __init__(self, source, news_repo):
        super().__init__(source, news_repo)
        self.special_urls = []

    def crawl_fresh_link(self):
        soup = self.fetch(self.source.full_url())
        links = self.extract_links(soup, self.LINK_SELECTOR)
        new_count = self.news_repo.add_pending(self.source, links)
        print(f"[{self.source.name}] Đã cào {new_count} bài mới...")

    def crawl_link_detail(self):
        pending = self.news_repo.get_pending(self.source.id)
        done = self.run_parallel(pending, self.crawl_detail)
        print(f"[{self.source.name}] Hoàn thiện {done}/{len(pending)} bài."
              f"(trong đó {len(self.special_urls)} bài đặc biệt chỉ có metadata).")

    # Xử lý tạm thời các bài không có văn bản
    # Nội dung (thuộc tính content) của thẻ <meta> đầu tiên có giá trị, thử lần lượt các selector.
    def get_meta(self, soup, *selectors):
        for selector in selectors:
            tag = soup.select_one(selector)
            if tag and tag.get("content", "").strip():
                return tag["content"].strip()
        return None

    # Lưu tiêu đề + tóm tắt + ngày đăng từ thẻ meta. Thiếu tiêu đề hoặc ngày đăng (không giống bài viết) -> False.
    def save_special(self, soup, article):
        title = self.get_meta(soup, 'meta[property="og:title"]')
        if not title and soup.title:
            title = soup.title.get_text(strip = True)
        published_at = self.parse_datetime(self.get_meta(soup, self.PUBLISHED_SELECTOR))
        if not title or published_at is None:
            return False
        saved = self.news_repo.update_detail(
            article.id,
            title,
            self.get_meta(soup, 'meta[property="og:description"]', 'meta[name="description"]'),
            SPECIAL_CONTENT_NOTE,
            None,
            published_at)
        # Chỉ nhận những trường hợp return >= 0
        # Nếu gặp lỗi khi lưu DB khiến bài viết 'pending' thì sẽ return -1
        return saved >= 0              

    # Bóc tách chi tiết 1 bài
    def crawl_detail(self, article):
        try:
            soup = self.fetch(article.url)          # dùng article.url, KHÔNG phải source_link
            if soup is None:
                return False
            title = self.first_text(soup, self.TITLE_SELECTOR)
            content = self.first_all_text(soup, self.CONTENT_SELECTOR) if title else None
            if not title or not content:
                # Không có thân bài dạng văn bản (video, podcast, định dạng khác): lưu tạm bằng metadata
                if self.save_special(soup, article):
                    self.special_urls.append(article.url)
                    print(f"[{self.source.name}] Bài đặc biệt, chỉ lưu metadata: {article.url}")
                    return True
                print(f"[{self.source.name}] Không lấy được nội dung và metadata: {article.url}")
                return False    
            # Lấy ngày đăng
            meta = soup.select_one(self.PUBLISHED_SELECTOR)
            published_at = self.parse_datetime(meta.get("content")) if meta else None
            saved = self.news_repo.update_detail(
                article.id,
                title,
                self.get_text(soup, self.SUMMARY_SELECTOR),
                content,
                self.get_text(soup, self.AUTHOR_SELECTOR),
                published_at
            )
            # Chỉ nhận những trường hợp return >= 0
            # Nếu gặp lỗi khi lưu DB khiến bài viết 'pending' thì sẽ return -1
            return saved >= 0
        except Exception as e:                      
            print(f"[{self.source.name}] Lỗi xử lý {article.url}: {e}")
            return False
    
    # def __init__(self):
    #     self.source_link = "https://vnexpress.net/"
    #     self.link = set()                         

    # def crawl_fresh_link(self):
    #     print("Crawl fresh link from VnExpress:")
    #     headers = {
    #         'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    #     }
    
    #     response = requests.get(self.source_link, headers=headers, timeout=10)
    #     soup = BeautifulSoup(response.text, 'html.parser')
    #     list_a_tag = soup.select('article h3.title-news a')
    #     set_link = set()
    #     for a in list_a_tag:
    #         set_link.add(a['href'].split('#')[0])
    #     self.link = set_link
        
    # def crawl_link_detail(self):
    #     print("Link detail from VnExpress")
    #     start_time = time.time()
    #     list_thread = []
    #     for a in self.link:
    #         t = threading.Thread(target=self.crawl_detail, args=[a])
    #         t.start()
    #         list_thread.append(t)
    #     for t in list_thread:
    #         t.join()
    #     end_time = time.time()
    #     print(f"Total time: {end_time - start_time} s")

    # def crawl_detail(self, link):
    #     headers = {
    #         'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    #     }
    #     print(f"Processing link: {link}")
    #     response = requests.get(self.source_link, headers=headers, timeout=10)
    #     soup = BeautifulSoup(response.text, 'html.parser')
    #     title_tag = soup.select_one('h1.title-detail a')        
    #     if(title_tag != None):
    #         news_title = title_tag.text
    #         print(news_title)
