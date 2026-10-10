from models.category import Category

class CategoryRepository:
    def __init__(self, db):
        self.db = db

    def get_all(self):
        rows = self.db.query(
            "SELECT id, name, description FROM categories "
            "WHERE deleted_at IS NULL ORDER BY id")
        return [Category(**r) for r in rows]