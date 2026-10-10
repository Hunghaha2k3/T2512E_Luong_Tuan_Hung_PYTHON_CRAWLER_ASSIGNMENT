import csv
import json
import os
from datetime import datetime

# Thư mục xuất file: <thư mục dự án>/exports (cố định, không phụ thuộc nơi chạy lệnh)
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXPORT_FOLDER = os.path.join(PROJECT_DIR, "exports")

# Thứ tự cột, phải TRÙNG tên các cột trong câu SELECT của NewsRepository.get_all_for_export
FIELDS = ["id", "source_name", "title", "url", "summary", "content",
          "author", "source_published_at", "created_at"]


class ExportService:
    def __init__(self, news_repo, folder=EXPORT_FOLDER):
        self.news_repo = news_repo
        self.folder = folder

    def _build_path(self, extension):
        """Tạo thư mục nếu chưa có, trả về đường dẫn file mới (tên có giờ nên không ghi đè)."""
        os.makedirs(self.folder, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return os.path.join(self.folder, f"tin_tuc_{stamp}.{extension}")

    # ---------- Tính năng 1: xuất CSV ----------
    def export_csv(self):
        """Trả về (đường dẫn file, số bài). Chưa có bài -> (None, 0). Lỗi ghi file -> OSError."""
        articles = self.news_repo.get_all_for_export()
        if not articles:
            return None, 0
        path = self._build_path("csv")
        # utf-8-sig: thêm BOM để Excel mở file hiển thị đúng tiếng Việt
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(articles)
        return path, len(articles)

    # ---------- Tính năng 2: xuất JSON ----------
    def export_json(self):
        """Trả về (đường dẫn file, số bài). Chưa có bài -> (None, 0). Lỗi ghi file -> OSError."""
        articles = self.news_repo.get_all_for_export()
        if not articles:
            return None, 0
        path = self._build_path("json")
        with open(path, "w", encoding="utf-8") as f:
            # ensure_ascii=False: giữ nguyên chữ có dấu; default=str: chuyển datetime thành chuỗi
            json.dump(articles, f, ensure_ascii=False, indent=2, default=str)
        return path, len(articles)