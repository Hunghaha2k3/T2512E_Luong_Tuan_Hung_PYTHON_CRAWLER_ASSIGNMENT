import json
import re
from services.crawler_service import CrawlerService

# Nội dung tạm cho những bài có định dạng đặc biệt (Không có văn bản trong HTML, định dạng video...)
# Query DB: content LIKE '[Bài đặc biệt]%'
SPECIAL_CONTENT_NOTE = ("[Bài đặc biệt] Không có nội dung văn bản trong HTML "
                        "(video hoặc định dạng khác). Xem bài gốc tại đường dẫn.")

class DantriCrawlerService(CrawlerService):
    DOMAIN = "dantri.com.vn"      

    # Link bài: thẻ <a> kết thúc .htm, rồi lọc theo mẫu /<chuyên-mục>/<slug>-<mã 14+ chữ số>.htm
    LINK_SELECTOR = 'a[href$=".htm"]'         # Selector thẻ <a> bài viết ở trang nguồn
    LINK_PATTERN = r"^https://dantri\.com\.vn/(?:[^/]+/)+[^/]+-\d{14,}\.htm$"       # Thêm Regex
    
    # Mỗi trường có DANH SÁCH selector: thử lần lượt, selector đầu tiên có kết quả thì dùng.
    # Mục 1: bài thường | Mục 2: bài dạng e-magazine (Thể thao, Tâm điểm, ...)
    TITLE_SELECTOR = ["h1"]
    SUMMARY_SELECTOR = ["article h1 ~ h2", "article h2.e-magazine__sapo"]        
    CONTENT_SELECTOR = ["article h1 ~ div p", "article div.e-magazine__body p"]
    AUTHOR_SELECTOR = ['article h1 ~ div a[href*="/tac-gia/"]', 
                       'article .e-magazine__info a[href*="/tac-gia/"]']
    PUBLISHED_SELECTOR = "time[datetime]"      # Thẻ <meta> chứa ngày ISO

    # Hàm xử lý các bài đặc biệt (chỉ lưu metadata) trong lượt chạy này
    def __init__(self, source, news_repo):
        super().__init__(source, news_repo)
        self.special_urls = []     

    # Nguồn là 1 chuyên mục (path khác '/') -> tiền tố URL của bài thuộc chuyên mục đó.
    def category_prefix(self):
        slug = self.source.path.strip("/")
        if slug.endswith(".htm"):
            slug = slug[:-4]
        return f"https://{self.source.domain}/{slug}/" if slug else None

    def crawl_fresh_link(self):
        soup = self.fetch(self.source.full_url())
        links = self.extract_links(soup, self.LINK_SELECTOR, self.LINK_PATTERN)
        prefix = self.category_prefix()
        # Chỉ giữ bài đúng chuyên mục của nguồn này
        if prefix:
            links = {link for link in links if link.startswith(prefix)} 
        new_count = self.news_repo.add_pending(self.source, links)
        print(f"[{self.source.name}] Đã cào {new_count} bài mới...")

    def crawl_link_detail(self):
        pending = self.news_repo.get_pending(self.source.id)
        done = self.run_parallel(pending, self.crawl_detail)
        print(f"[{self.source.name}] Hoàn thiện {done}/{len(pending)} bài."
              f"(trong đó {len(self.special_urls)} bài đặc biệt chỉ có metadata).")

    # Xử lý tạm thời các bài không có văn bản
    def get_meta(self, soup, prop):
        tag = soup.select_one(f'meta[property="{prop}"]')
        return tag.get("content", "").strip() if tag else None

    # Đọc biến JSON window.wDataLayer trong thẻ <script> (có ngày đăng, tác giả). Lỗi -> {}
    def get_data_layer(self, soup):
        for script in soup.find_all("script"):
            match = re.search(r"window\.wDataLayer\s*=\s*(\{.*?\})\s*;", script.get_text(), re.S)
            if match:
                try:
                    return json.loads(match.group(1))
                except ValueError:
                    return {}
        return {}

    # Lưu thông tin các bài có định dạng đặc biệt
    # Lưu tiêu đề + tóm tắt từ thẻ meta, ngày đăng + tác giả từ wDataLayer. Không phải bài viết -> False.
    def save_special(self, soup, article):
        title = self.get_meta(soup, "og:title")
        if not title or self.get_meta(soup, "og:type") != "article":
            return False
        data = self.get_data_layer(soup)
        author = (data.get("author_id") or "").strip() or None
        saved = self.news_repo.update_detail(
            article.id,
            title,
            self.get_meta(soup, "og:description"),
            SPECIAL_CONTENT_NOTE,
            author,
            self.parse_datetime(data.get("published_date")))
        # Chỉ nhận những trường hợp return >= 0
        # Nếu gặp lỗi khi lưu DB khiến bài viết 'pending' thì sẽ return -1
        return saved >= 0              

    # Bóc tách chi tiết 1 bài
    def crawl_detail(self, article):
        try:
            soup = self.fetch(article.url)
            if soup is None:
                return False
            # Tiêu đề: thẻ h1; nếu h1 rỗng hoặc không có thì dùng thẻ meta og:title (trùng h1 ở bài thường)
            title = self.first_text(soup, self.TITLE_SELECTOR) or self.get_meta(soup, "og:title")
            content = self.first_all_text(soup, self.CONTENT_SELECTOR)
            # Không có thân bài dạng văn bản (video, định dạng khác) -> lưu tạm bằng metadata
            if not title or not content:
                if self.save_special(soup, article):
                    self.special_urls.append(article.url)
                    print(f"[{self.source.name}] Bài đặc biệt, chỉ lưu metadata: {article.url}")
                    return True
                print(f"[{self.source.name}] Không lấy được nội dung và metadata: {article.url}")
                return False
            time_tag = soup.select_one(self.PUBLISHED_SELECTOR)
            if time_tag:
                published_at = self.parse_datetime(time_tag.get("datetime"))
            else:                      # dự phòng: ngày đăng trong biến wDataLayer
                published_at = self.parse_datetime(self.get_data_layer(soup).get("published_date"))
            saved = self.news_repo.update_detail(
                article.id,
                title,
                self.first_text(soup, self.SUMMARY_SELECTOR),
                content,
                self.first_all_text(soup, self.AUTHOR_SELECTOR),
                published_at
            )
            # Chỉ nhận những trường hợp return >= 0
            # Nếu gặp lỗi khi lưu DB khiến bài viết 'pending' thì sẽ return -1
            return saved >= 0
        except Exception as e:
            print(f"[{self.source.name}] Lỗi xử lý {article.url}: {e}")
            return False