from models.source import Source

# Hằng số cố định trong code (không phải dữ liệu người dùng) nên ghép vào f-string an toàn
COLUMNS = ("id, name, domain, path, category_id, status, description, link_selector, "
           "title_selector, description_selector, content_selector, image_selector, "
           "author_selector, comment_selector, remove_selector")

# Class chứa các lệnh thao tác (Thêm/Sửa/Xóa...)
class SourceRepository:
    def __init__(self, db):
        self.db = db

    def get_all(self):
        rows = self.db.query(
            f"SELECT {COLUMNS} FROM sources WHERE deleted_at IS NULL ORDER BY id")
        return [Source(**r) for r in rows]

    def get_active(self):
        rows = self.db.query(
            f"SELECT {COLUMNS} FROM sources "
            "WHERE deleted_at IS NULL AND status = 'active' ORDER BY id")
        return [Source(**r) for r in rows]

    def get_by_id(self, source_id):
        rows = self.db.query(
            f"SELECT {COLUMNS} FROM sources WHERE id = %s AND deleted_at IS NULL",
            (source_id,))
        return Source(**rows[0]) if rows else None

    def add(self, s):   # s: Source; s.id truyền 0, không dùng tới
        sql = """INSERT INTO sources (name, domain, path, category_id, link_selector,
                 title_selector, description_selector, content_selector, author_selector)
                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        return self.db.execute(sql, (s.name, s.domain, s.path, s.category_id,
                                     s.link_selector, s.title_selector,
                                     s.description_selector, s.content_selector,
                                     s.author_selector))

    def update(self, s):
        sql = """UPDATE sources SET name=%s, domain=%s, path=%s, category_id=%s,
                 link_selector=%s, title_selector=%s, description_selector=%s,
                 content_selector=%s, author_selector=%s
                 WHERE id=%s AND deleted_at IS NULL"""
        return self.db.execute(sql, (s.name, s.domain, s.path, s.category_id,
                                     s.link_selector, s.title_selector,
                                     s.description_selector, s.content_selector,
                                     s.author_selector, s.id))

    def toggle_status(self, source_id):
        sql = ("UPDATE sources SET status = IF(status = 'active', 'deactive', 'active') "
               "WHERE id = %s AND deleted_at IS NULL")
        return self.db.execute(sql, (source_id,))

    def soft_delete(self, source_id):
        sql = ("UPDATE sources SET deleted_at = NOW() "
               "WHERE id = %s AND deleted_at IS NULL")
        return self.db.execute(sql, (source_id,))

    def count_articles(self, source_id):
        rows = self.db.query(
            "SELECT COUNT(*) AS total FROM articles "
            "WHERE source_id = %s AND deleted_at IS NULL", (source_id,))
        return rows[0]["total"] if rows else 0