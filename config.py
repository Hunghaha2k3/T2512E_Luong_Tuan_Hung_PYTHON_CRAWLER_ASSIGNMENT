import os
from pathlib import Path

# Đọc file .env (mỗi dòng KEY=giá_trị) và nạp vào biến môi trường.
# Biến đã được đặt sẵn trong hệ thống thì được ưu tiên, file .env không ghi đè.
def load_env_file(path):
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))

# Luôn đọc file .env nằm cạnh config.py (trong thư mục dự án), không phụ thuộc terminal đang đứng ở đâu
load_env_file(Path(__file__).resolve().parent / ".env")

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "dynamic_crawler_db"),
}

# Bot 3: AI viết lại bài (Google AI Studio / Gemini API)
GEMINI_CONFIG = {
    "api_key": os.getenv("GEMINI_API_KEY", ""),
    # Tên model đặt trong file .env, có thể thay đổi
    "model": os.getenv("GEMINI_MODEL", ""),
}
REWRITE_BATCH_SIZE = 5          # Số bài tối đa mỗi lượt chạy bot 3
REWRITE_DELAY_SECONDS = 6       # Nghỉ giữa 2 lần gọi AI (tránh vượt giới hạn tốc độ của gói miễn phí)
REWRITE_MAX_ATTEMPTS = 3        # Số lần thử tối đa cho 1 bài bị lỗi