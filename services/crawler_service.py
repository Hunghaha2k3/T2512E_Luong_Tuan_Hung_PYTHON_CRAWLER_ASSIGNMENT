import importlib
import re
import os
import pkgutil
import requests
import time

from concurrent.futures import ThreadPoolExecutor
from abc import ABC,abstractmethod
from urllib.parse import urljoin
from datetime import datetime
from bs4 import BeautifulSoup

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

class CrawlerService(ABC):
    # Khai báo DOMAIN
    DOMAIN = None 

    # Thêm cấu hình tốc độ để giảm thiểu lỗi 429 (Too many requests)
    MAX_WORKERS = 2          # Số luồng tải song song
    REQUEST_DELAY = 2.0      # Request Interval (khoảng nghỉ giữa 2 lượt Request)
    MAX_RETRIES = 3          # Số lượt Retries khi bị Rate Limit
    RETRY_DELAY = 5          # Retries Interval (khoảng nghỉ giữa 2 lượt Retry)

    def __init__(self, source, news_repo):
        self.source = source            # Đối tượng Source
        self. news_repo = news_repo

    # Hàm Rate Limit (bổ sung thêm để tránh lỗi 429)
    def is_rate_limited(self, soup):
        parts = [t.get_text("", strip = True) for t in (soup.find("h1"), soup.find("title")) if t]
        return "too many requests" in " ".join(parts).lower()

    # Các hàm dùng chung mọi nguồn)
    # Tải trang, trả về BeautifulSoup. Lỗi mạng/HTTP -> in cảnh báo, trả về None
    # Bổ sung thêm rate limit trong hàm
    def fetch(self, url):
        for attempt in range(1, self.MAX_RETRIES + 1):
            time.sleep(self.REQUEST_DELAY)
            try: 
                res = requests.get(url, headers = headers, timeout = 10)
                soup = BeautifulSoup(res.text, "html.parser")
                # Bị chặn: mã 429 thật, hoặc mã 200 nhưng nội dung là trang chặn
                if res.status_code == 429 or self.is_rate_limited(soup):
                    wait = self.RETRY_DELAY * attempt
                    print(f" Nguồn [{self.source.name}] hiện đang bị giới hạn tốc độ (Mã lỗi 429)! Vui lòng chờ {wait}s rồi thử lại!" 
                          f"({attempt}/{self.MAX_RETRIES}): {url}")
                    time.sleep(wait)
                    continue
                res.raise_for_status()
                return soup
            except requests.exceptions.HTTPError as e:
                print(f"[{self.source.name}] Lỗi HTTP {e.response.status_code}: {url}]")
                return None
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                print(f"[{self.source.name}] Mất kết nối hoặc quá thời gian ({type(e).__name__}): {url}")
                return None
            except requests.exceptions.RequestException as e:
                print(f"[{self.source.name}] Lỗi request: {e}")
                return None
        print(f"[{self.source.name}] Vẫn bị giới hạn tốc độ sau {self.MAX_RETRIES} lần thử, bỏ qua: {url}")
        return None

    # Lấy tập link tuyệt đối từ các thẻ <a> khớp selector.
    # Bổ sung thêm pattern (regex): chỉ giữ link khớp mẫu này
    def extract_links(self, soup, selector, pattern = None):
        links = set()
        if soup is None or not selector:
            return links
        for a in soup.select(selector):
            href = a.get("href")
            if not href:
                continue
            link = urljoin(self.source.full_url(), href).split("#")[0]
            if pattern and not re.search(pattern, link):
                continue
            links.add(link)
        return links

    def get_text(self, soup, selector):
        tag = soup.select_one(selector) if selector else None
        return tag.get_text("", strip = True) if tag else None

    # Nối text của MỌI phần tử khớp selector, bỏ đoạn rỗng và đoạn trùng (giữ thứ tự).
    def get_all_text(self, soup, selector):
        if not selector:
            return None
        parts = []
        for tag in soup.select(selector):
            text = tag.get_text(" ", strip=True)
            if text and text not in parts:
                parts.append(text)
        return "\n".join(parts) if parts else None

    # Thử lần lượt từng selector, trả về text đầu tiên KHÔNG RỖNG trong các phần tử khớp. Không có -> None.
    def first_text(self, soup, selectors):
        for selector in selectors:
            for tag in soup.select(selector):
                text = tag.get_text(" ", strip = True)
                if text:
                    return text
        return None

    # Thử lần lượt từng selector, trả về nội dung của selector đầu tiên có kết quả.
    def first_all_text(self, soup, selectors):
        for selector in selectors:
            text = self.get_all_text(soup, selector)
            if text:
                return text
        return None

    # Chuỗi ngày-giờ -> datetime (bỏ múi giờ). 
    # Đọc được dạng ISO '2026-10-07T11:33:15+07:00' lẫn dạng có khoảng trắng quanh múi giờ '2026-10-07 06:01 + 07:00'. Lỗi -> None.
    def parse_datetime(self, value):
        if not value:
            return None
        text = re.sub(r"\s*([+-])\s*(\d{2}:\d{2})\s*$", r"\1\2", value.strip())
        try:
            return datetime.fromisoformat(text).replace(tzinfo=None)    # cột DATETIME không lưu múi giờ
        except (TypeError, ValueError):
            return None
        
    # Chạy func cho từng phần tử bằng nhiều luồng, trả về số lần func trả về True.
    def run_parallel(self, items, func, max_workers = None):
        with ThreadPoolExecutor(max_workers = max_workers or self.MAX_WORKERS) as pool:
            results = list(pool.map(func, items))
        return sum(1 for r in results if r)
    
    # Làm nhiệm vụ bot1: 
    # Hàng ngày vào 8h00 vào trang lấy url và id của bài viết
    # Đảm bảo link không bị trùng
    # Lưu vào db với trạng thái PENDING
    @abstractmethod
    def crawl_fresh_link(self):
        pass

    # Làm nhiệm vụ bot2:
    # Lấy danh sách bài viết chưa hoàn thiện ở db, bóc tách các trường dữ liệu
    # Save article với trạng thái là COMPLETE
    @abstractmethod
    def crawl_link_detail(self):
        pass


# (Bổ sung) Cơ chế tự nạp file nguồn
_crawlers_loaded = False

# Nạp mọi file *_crawler_service.py trong thư mục services (chỉ chạy 1 lần).
def load_all_crawlers():
    global _crawlers_loaded
    if _crawlers_loaded:
        return
    _crawlers_loaded = True
    folder = os.path.dirname(__file__)
    for module_info in pkgutil.iter_modules([folder]):
        if module_info.name.endswith("_crawler_service"):
            try:
                importlib.import_module(f"services.{module_info.name}")
            except Exception as e:       # Cấu hình sao cho 1 file có bị lỗi cũng không sập các nguồn khác
                print(f"Không nạp được {module_info.name}: {e}")

# Tìm class có DOMAIN khớp source.domain, trả về đối tượng crawler. Không có -> None.
def create_crawler(source, news_repo):
    load_all_crawlers()
    for cls in CrawlerService.__subclasses__():
        if cls.DOMAIN == source.domain.lower():
            return cls(source, news_repo)
    return None