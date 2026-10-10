class ArticleRewrite:
    def __init__(self, id, article_id, title = None, summary = None, content = None, status = "failed", error_message = None, attempts = 0, ai_model = None, input_tokens = None, output_tokens = None, rewritten_at = None, created_at = None):
        self.id = id
        self.article_id = article_id
        self.title = title
        self.summary = summary
        self.content = content
        self.status = status
        self.error_message = error_message
        self.attempts = attempts
        self.ai_model = ai_model
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.rewritten_at = rewritten_at
        self.created_at = created_at
        