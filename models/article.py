class Article:
    def __init__(self, id, source_id, category_id, url, slug, status="pending",
                 title=None, summary=None, content=None, author=None,
                 source_published_at=None, created_at=None):
        self.id = id
        self.source_id = source_id
        self.category_id = category_id
        self.url = url
        self.slug = slug
        self.status = status
        self.title = title
        self.summary = summary
        self.content = content
        self.author = author
        self.source_published_at = source_published_at
        self.created_at = created_at