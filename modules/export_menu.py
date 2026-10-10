class ExportMenu:
    def __init__(self, export_service):
        self.export_service = export_service

    def run(self):
        while True:
            print("\n--- XUẤT FILE ---")
            print("2.6.1. Xuất định dạng CSV")
            print("2.6.2. Xuất định dạng JSON")
            print("0. Quay lại Menu quản lý tin tức")
            choice = input("Chọn: ").strip()
            if choice == "1":
                self.export("CSV", self.export_service.export_csv)
            elif choice == "2":
                self.export("JSON", self.export_service.export_json)
            elif choice == "0":
                break
            else:
                print("Lựa chọn không hợp lệ.")

    def export(self, label, export_func):
        try:
            path, total = export_func()
        except OSError as e:
            print(f"Lỗi ghi file {label}: {e}")
            return
        if path is None:
            print("Chưa có bài viết nào để xuất.")
            return
        print(f"Đã xuất {total} bài viết ra file {label}: {path}")