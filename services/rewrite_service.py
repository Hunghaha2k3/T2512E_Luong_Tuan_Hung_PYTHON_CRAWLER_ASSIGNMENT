import time

from services.gemini_client import AIArticleError, AIFatalError, AITemporaryError

MAX_TEMP_STREAK = 3     # số bài liên tiếp không gọi được AI thì dừng lượt chạy (có thể đã hết hạn mức)

# Bot 3: lấy các bài đã cào, nhờ AI viết lại, lưu vào bảng article_rewrite.
class RewriteService:
    def __init__(self, rewrite_repo, ai_client, delay=6, max_attempts=3):
        self.rewrite_repo = rewrite_repo
        self.ai_client = ai_client
        self.delay = delay                  # giây nghỉ giữa 2 lần gọi AI
        self.max_attempts = max_attempts    # số lần thử tối đa cho 1 bài bị lỗi

    # Chạy 1 lượt. Trả về dict: completed, failed, skipped, aborted.
    def run(self, limit):
        result = {"completed": 0, "failed": 0, "skipped": 0, "aborted": False}
        articles = self.rewrite_repo.get_articles_to_rewrite(limit, self.max_attempts)
        if not articles:
            print("[Bot 3] Không có bài nào cần viết lại.")
            return result
        print(f"[Bot 3] Có {len(articles)} bài sẽ được viết lại bằng mô hình {self.ai_client.model}.")

        temp_streak = 0
        for index, article in enumerate(articles, 1):
            label = f"[Bot 3] ({index}/{len(articles)}) Bài ID {article['id']}"
            try:
                data = self.ai_client.rewrite(article["title"], article["summary"], article["content"])
            except AIFatalError as e:
                print(f"{label}: lỗi cấu hình AI, dừng lượt chạy: {e}")
                result["aborted"] = True
                break
            except AITemporaryError as e:
                result["skipped"] += 1
                temp_streak += 1
                print(f"{label}: AI tạm thời không phản hồi, bỏ qua (không ghi lỗi): {e}")
                if temp_streak >= MAX_TEMP_STREAK:
                    print(f"[Bot 3] {MAX_TEMP_STREAK} bài liên tiếp không gọi được AI "
                          "(có thể đã hết hạn mức). Dừng lượt chạy.")
                    result["aborted"] = True
                    break
            except AIArticleError as e:
                temp_streak = 0
                self.rewrite_repo.save_failure(article["id"], str(e), self.ai_client.model)
                result["failed"] += 1
                print(f"{label}: THẤT BẠI - {e}")
            else:
                temp_streak = 0
                saved = self.rewrite_repo.save_success(
                    article["id"], data["title"], data["summary"], data["content"],
                    self.ai_client.model, data["input_tokens"], data["output_tokens"])
                if saved < 0:
                    result["failed"] += 1
                    print(f"{label}: AI viết xong nhưng không ghi được vào DB")
                else:
                    result["completed"] += 1
                    print(f"{label}: xong - \"{data['title'][:60]}\" "
                          f"({data['input_tokens']} token vào, {data['output_tokens']} token ra)")
            if index < len(articles):
                time.sleep(self.delay)

        print(f"[Bot 3] Kết thúc: {result['completed']} bài xong, {result['failed']} bài lỗi, "
              f"{result['skipped']} bài bỏ qua" + (" (lượt chạy bị dừng giữa chừng)." if result["aborted"] else "."))
        return result