from models.source import Source
from modules.utils import read_int, read_required, read_optional, read_keep, print_table


def clean_domain(domain):
    return domain.replace("https://", "").replace("http://", "").strip("/")


class SourceMenu:
    def __init__(self, source_repo, category_repo):
        self.source_repo = source_repo
        self.category_repo = category_repo

    def run(self):
        while True:
            print("\n--- QUẢN LÝ NGUỒN TIN ---")
            print("1.1. Xem danh sách các nguồn tin")
            print("1.2. Thêm nguồn tin mới")
            print("1.3. Cập nhật thông tin nguồn tin")
            print("1.4. Xóa nguồn tin")
            print("1.5. Đổi trạng thái Kích hoạt/Bỏ kích hoạt")
            print("0. Quay lại Menu chính")
            choice = input("Chọn: ").strip()
            if choice == "1":
                self.show_list()
            elif choice == "2":
                self.add_source()
            elif choice == "3":
                self.update_source()
            elif choice == "4":
                self.delete_source()
            elif choice == "5":
                self.toggle_source()
            elif choice == "0":
                break
            else:
                print("Lựa chọn không hợp lệ.")

    def show_list(self):
        sources = self.source_repo.get_all()
        if not sources:
            print("Chưa có nguồn tin nào.")
            return
        rows = [(s.id, s.name, s.full_url(), "Active" if s.is_active() else "Inactive")
                for s in sources]
        print_table(["ID", "Tên nguồn", "URL", "Trạng thái"], rows, [6, 20, 45, 12])

    def choose_category_id(self):
        categories = self.category_repo.get_all()
        if not categories:
            print("Chưa có chuyên mục nào trong DB.")
            return None
        print_table(["ID", "Chuyên mục"], [(c.id, c.name) for c in categories], [6, 30])
        valid_ids = [c.id for c in categories]
        while True:
            category_id = read_int("Chọn ID chuyên mục: ")
            if category_id in valid_ids:
                return category_id
            print("ID chuyên mục không tồn tại.")

    def add_source(self):
        print("--- Thêm nguồn tin mới (Enter để bỏ qua ô không bắt buộc) ---")
        name = read_required("Tên nguồn: ")
        domain = clean_domain(read_required("Domain (vd: vnexpress.net): "))
        path = read_required("Path (vd: /): ")
        category_id = self.choose_category_id()
        if category_id is None:
            return
        source = Source(0, name, domain, path, category_id,
                        link_selector=read_optional("Link selector: "),
                        title_selector=read_optional("Title selector: "),
                        description_selector=read_optional("Description selector: "),
                        content_selector=read_optional("Content selector: "),
                        author_selector=read_optional("Author selector: "))
        result = self.source_repo.add(source)
        print("Thêm nguồn thành công." if result > 0 else "Thêm nguồn thất bại.")

    def update_source(self):
        source = self.source_repo.get_by_id(read_int("Nhập ID nguồn cần sửa: "))
        if source is None:
            print("Không tìm thấy nguồn.")
            return
        print("(Enter = giữ nguyên giá trị hiện tại)")
        source.name = read_keep("Tên nguồn", source.name)
        source.domain = clean_domain(read_keep("Domain", source.domain))
        source.path = read_keep("Path", source.path)
        source.link_selector = read_keep("Link selector", source.link_selector)
        source.title_selector = read_keep("Title selector", source.title_selector)
        source.description_selector = read_keep("Description selector", source.description_selector)
        source.content_selector = read_keep("Content selector", source.content_selector)
        source.author_selector = read_keep("Author selector", source.author_selector)
        result = self.source_repo.update(source)
        print("Cập nhật thành công." if result >= 0 else "Cập nhật thất bại.")

    def toggle_source(self):
        source_id = read_int("Nhập ID nguồn cần đổi trạng thái: ")
        if self.source_repo.get_by_id(source_id) is None:
            print("Không tìm thấy nguồn.")
            return
        self.source_repo.toggle_status(source_id)
        updated = self.source_repo.get_by_id(source_id)
        print(f"Trạng thái mới của '{updated.name}': {updated.status}")

    def delete_source(self):
        source_id = read_int("Nhập ID nguồn cần xóa: ")
        source = self.source_repo.get_by_id(source_id)
        if source is None:
            print("Không tìm thấy nguồn.")
            return
        total = self.source_repo.count_articles(source_id)
        print(f"Nguồn '{source.name}' ({source.full_url()}) đang có {total} bài viết (bài viết sẽ được giữ lại).")
        if input("Xác nhận xóa nguồn? (y/n): ").strip().lower() != "y":
            print(f"Đã hủy thao tác xóa nguồn. Nguồn {source.name} vẫn tồn tại.")
            return
        result = self.source_repo.soft_delete(source_id)
        print(f"Đã xóa nguồn {source.name}." if result > 0 else "Xóa thất bại.")