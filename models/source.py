class Source:
    def __init__(self, id, name, domain, path, category_id, status="active",
                 description=None, link_selector=None, title_selector=None,
                 description_selector=None, content_selector=None,
                 image_selector=None, author_selector=None,
                 comment_selector=None, remove_selector=None):
        self.id = id
        self.name = name
        self.domain = domain
        self.path = path
        self.category_id = category_id
        self.status = status
        self.description = description
        self.link_selector = link_selector
        self.title_selector = title_selector
        self.description_selector = description_selector
        self.content_selector = content_selector
        self.image_selector = image_selector
        self.author_selector = author_selector
        self.comment_selector = comment_selector
        self.remove_selector = remove_selector

    def full_url(self):
        return f"https://{self.domain}{self.path}"

    def is_active(self):
        return self.status == "active"

    def __str__(self):
        return f"Source({self.id}, {self.name}, {self.full_url()}, {self.status})"