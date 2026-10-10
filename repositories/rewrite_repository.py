from models.article_rewrite import ArticleRewrite

# Điều kiện một bài gốc "cần viết lại": 
#   1. Đã cào xong, có nội dung văn bản thật (không phải bài đặc biệt).
#   2. Chưa bị xóa, và CHƯA có bản viết lại (hoặc bản viết lại bị lỗi nhưng chưa quá số lần thử).
ELIGIBLE_FROM_WHERE = (
    "FROM articles a LEFT JOIN article_rewrite r ON r.article_id = a.id "
    "WHERE a.status = 'completed' AND a.deleted_at IS NULL "
    "AND a.content IS NOT NULL AND a.content NOT LIKE %s "
    "AND (r.id IS NULL OR r.deleted_at IS NOT NULL "
    "OR (r.status = 'failed' AND r.attempts < %s))")
SPECIAL_PATTERN = "[Bài đặc biệt]%"

COLUMNS = ("id, article_id, title, summary, content, status, error_message, attempts, "
           "ai_model, input_tokens, output_tokens, rewritten_at, created_at")


class RewriteRepository:
    def __init__(self, db):
        self.db = db

    # Lấy danh sách bài cần viết lại
    def get_articles_to_rewrite(self, limit, max_attempts):
        """Trả về list[dict]: id, title, summary, content của các bài cần viết lại (cũ nhất trước)."""
        sql = ("SELECT a.id, a.title, a.summary, a.content " + ELIGIBLE_FROM_WHERE +
               " ORDER BY a.id LIMIT %s")
        return self.db.query(sql, (SPECIAL_PATTERN, max_attempts, limit))

    def count_waiting(self, max_attempts):
        rows = self.db.query("SELECT COUNT(*) AS total " + ELIGIBLE_FROM_WHERE,
                             (SPECIAL_PATTERN, max_attempts))
        return rows[0]["total"] if rows else 0

    # Lưu kết quả (mỗi bài gốc chỉ có 1 dòng: lưu lại thì cập nhật dòng đó)
    def save_success(self, article_id, title, summary, content, ai_model, input_tokens, output_tokens):
        sql = ("INSERT INTO article_rewrite (article_id, title, summary, content, status, error_message, "
               "attempts, ai_model, input_tokens, output_tokens, rewritten_at) "
               "VALUES (%s, %s, %s, %s, 'completed', NULL, 1, %s, %s, %s, NOW()) "
               "ON DUPLICATE KEY UPDATE title = VALUES(title), summary = VALUES(summary), "
               "content = VALUES(content), status = 'completed', error_message = NULL, "
               "attempts = attempts + 1, ai_model = VALUES(ai_model), "
               "input_tokens = VALUES(input_tokens), output_tokens = VALUES(output_tokens), "
               "rewritten_at = NOW(), deleted_at = NULL")
        return self.db.execute(sql, (article_id, title, summary, content, ai_model,
                                     input_tokens, output_tokens))

    def save_failure(self, article_id, error_message, ai_model):
        sql = ("INSERT INTO article_rewrite (article_id, status, error_message, attempts, ai_model) "
               "VALUES (%s, 'failed', %s, 1, %s) "
               "ON DUPLICATE KEY UPDATE status = 'failed', error_message = VALUES(error_message), "
               "attempts = attempts + 1, ai_model = VALUES(ai_model), deleted_at = NULL")
        return self.db.execute(sql, (article_id, error_message[:500], ai_model))

    # Theo dõi
    def get_stats(self):
        """Số bài, tổng token theo trạng thái: {'completed': {...}, 'failed': {...}}."""
        rows = self.db.query(
            "SELECT status, COUNT(*) AS so_bai, COALESCE(SUM(input_tokens), 0) AS tong_input, "
            "COALESCE(SUM(output_tokens), 0) AS tong_output "
            "FROM article_rewrite WHERE deleted_at IS NULL GROUP BY status")
        return {r["status"]: r for r in rows}

    def get_failed(self, limit=10):
        rows = self.db.query(
            f"SELECT {COLUMNS} FROM article_rewrite "
            "WHERE status = 'failed' AND deleted_at IS NULL ORDER BY updated_at DESC LIMIT %s", (limit,))
        return [ArticleRewrite(**r) for r in rows]