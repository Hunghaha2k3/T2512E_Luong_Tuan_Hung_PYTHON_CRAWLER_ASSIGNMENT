from urllib.parse import urlparse
from models.article import Article

def make_slug(url):
    last_part = urlparse(url).path.rstrip("/").split("/")[-1]
    return last_part.rsplit(".", 1)[0][:255]          # bỏ đuôi .html để tạo chuỗi slug hiển thị

class NewsRepository:
    def __init__(self, db):
        self.db = db

    # Repo cho Crawler
    def add_pending(self, source, links):
        sql = ("INSERT IGNORE INTO articles (source_id, category_id, url, slug, status) "
               "VALUES (%s, %s, %s, %s, 'pending')")
        new_count = 0
        for link in links:
            if self.db.execute(sql, (source.id, source.category_id, link, make_slug(link))) > 0:
                new_count += 1        # rowcount = 0 nghĩa là URL trùng nên sẽ bỏ qua
        return new_count

    def get_pending(self, source_id):
        rows = self.db.query(
            "SELECT id, source_id, category_id, url, slug, status FROM articles "
            "WHERE source_id = %s AND status = 'pending' AND deleted_at IS NULL",
            (source_id,))
        return [Article(**r) for r in rows]

    def update_detail(self, article_id, title, summary, content, author, published_at):
        sql = ("UPDATE articles SET title=%s, summary=%s, content=%s, author=%s, "
               "source_published_at=%s, status='completed' WHERE id=%s")
        return self.db.execute(sql, (title, summary, content, author, published_at, article_id))

    # Repo cho Menu
    def _build_where(self, keyword=None, source_id=None, crawl_date=None):
        where = ["a.deleted_at IS NULL", "a.status = 'completed'"]
        params = []
        if keyword:
            where.append("(a.title LIKE %s OR a.content LIKE %s)")
            params += [f"%{keyword}%", f"%{keyword}%"]
        if source_id:
            where.append("a.source_id = %s")
            params.append(source_id)
        if crawl_date:                                  # chuỗi 'YYYY-MM-DD'
            where.append("DATE(a.created_at) = %s")
            params.append(crawl_date)
        return " AND ".join(where), params

    def get_page(self, offset, limit, **filters):
        where, params = self._build_where(**filters)
        sql = ("SELECT a.id, a.title, s.name AS source_name, a.created_at "
               "FROM articles a JOIN sources s ON a.source_id = s.id "
               f"WHERE {where} ORDER BY a.id DESC LIMIT %s OFFSET %s")
        return self.db.query(sql, params + [limit, offset])      # list[dict]

    def count(self, **filters):
        where, params = self._build_where(**filters)
        rows = self.db.query(f"SELECT COUNT(*) AS total FROM articles a WHERE {where}", params)
        return rows[0]["total"] if rows else 0

    def get_detail(self, article_id):
        rows = self.db.query(
            "SELECT a.id, a.title, a.summary, a.content, a.url, a.source_published_at, "
            "s.name AS source_name "
            "FROM articles a JOIN sources s ON a.source_id = s.id "
            "WHERE a.id = %s AND a.deleted_at IS NULL", (article_id,))
        return rows[0] if rows else None

    def soft_delete(self, article_id):
        return self.db.execute(
            "UPDATE articles SET status='deleted', deleted_at=NOW() "
            "WHERE id=%s AND deleted_at IS NULL", (article_id,))

    def soft_delete_older_than(self, days):
        return self.db.execute(
            "UPDATE articles SET status='deleted', deleted_at=NOW() "
            "WHERE created_at < NOW() - INTERVAL %s DAY AND deleted_at IS NULL", (days,))

    def get_all_for_export(self):
        sql = ("SELECT a.id, s.name AS source_name, a.title, a.url, a.summary, a.content, "
               "a.author, a.source_published_at, a.created_at "
               "FROM articles a JOIN sources s ON a.source_id = s.id "
               "WHERE a.deleted_at IS NULL AND a.status = 'completed' "
               "ORDER BY a.id")
        return self.db.query(sql)