import time

import requests

from config import GEMINI_CONFIG
from services.gemini_client import AIArticleError, AIFatalError, AITemporaryError, GeminiClient

key = GEMINI_CONFIG["api_key"]
model = GEMINI_CONFIG["model"]
if not key:
    print("Chưa có khóa. Mở file .env trong thư mục dự án và điền dòng:  GEMINI_API_KEY=khóa-của-bạn")
    raise SystemExit(1)
print(f"Đã thấy khóa API (độ dài {len(key)} ký tự, không in ra màn hình).")
print(f"Model cấu hình trong .env: {model or '(chưa đặt)'}")

# Bỏ qua các model không dùng để sinh văn bản
LOAI_TRU = ("image", "tts", "live", "audio", "embed", "robot", "computer", "customtools", "banana")
HEADERS = {"x-goog-api-key": key, "Content-Type": "application/json"}

print("\n=== 1. Danh sách model Google trả về cho khóa của bạn ===")
res = requests.get(f"{GeminiClient.BASE_URL}/models", headers=HEADERS, params={"pageSize": 200}, timeout=30)
print("HTTP", res.status_code)
if res.status_code != 200:
    print("Phản hồi:", res.text[:500])
    raise SystemExit(1)
names = [m["name"].replace("models/", "") for m in res.json().get("models", [])
         if "generateContent" in m.get("supportedGenerationMethods", [])]
print(f"Có {len(names)} model hỗ trợ generateContent:")
for name in names:
    print("  -", name)
print("LƯU Ý: có tên trong danh sách chưa chắc đã dùng được (model cũ vẫn có thể nằm trong danh sách).")

print("\n=== 2. Thử gọi thật từng model (mỗi model 1 yêu cầu rất ngắn) ===")
if model:      # đã chọn model trong .env: chỉ thử đúng model đó để tiết kiệm hạn mức
    ung_vien = [model]
else:          # chưa chọn: quét các model flash để tìm model dùng được
    ung_vien = [n for n in names if n.startswith("gemini-") and "flash" in n
                and not any(w in n for w in LOAI_TRU)][:12]
print(f"Sẽ thử {len(ung_vien)} model: {', '.join(ung_vien)}")
dung_duoc = []
for name in ung_vien:
    payload = {"contents": [{"role": "user", "parts": [{"text": "Chỉ trả lời một từ: OK"}]}],
               "generationConfig": {"maxOutputTokens": 16}}
    try:
        r = requests.post(f"{GeminiClient.BASE_URL}/models/{name}:generateContent",
                          headers=HEADERS, json=payload, timeout=60)
        if r.status_code == 200:
            dung_duoc.append(name)
            ket_qua = "DÙNG ĐƯỢC"
        else:
            ket_qua = f"HTTP {r.status_code}: {GeminiClient.error_message(r)[:90]}"
    except requests.exceptions.RequestException as loi:
        ket_qua = f"lỗi mạng ({type(loi).__name__})"
    print(f"  {name:36} -> {ket_qua}")
    time.sleep(2)

print("\nModel dùng được:", ", ".join(dung_duoc) if dung_duoc else "(không có model nào)")
if not dung_duoc:
    if model:
        print(f"\nModel trong .env ({model}) không dùng được. Xóa phần sau 'GEMINI_MODEL=' trong .env "
              "rồi chạy lại để quét các model khác, hoặc thử một tên model khác.")
    else:
        print("Gửi mình nguyên phần kết quả ở trên (không gồm khóa) để xem tiếp.")
    raise SystemExit(1)
if not model:
    print("\nChưa đặt GEMINI_MODEL trong .env. Mở file .env, chọn một model ở trên và sửa dòng, ví dụ:")
    print(f"    GEMINI_MODEL={dung_duoc[0]}")
    print("rồi chạy lại script này để thử viết lại bài mẫu.")
    raise SystemExit(0)

print(f"\n=== 3. Viết lại thử một đoạn ngắn bằng model {model} ===")
client = GeminiClient(key, model)
try:
    ket_qua = client.rewrite(
        "Hà Nội đón đợt không khí lạnh đầu mùa",
        "Nhiệt độ giảm mạnh từ đêm nay.",
        "Theo Trung tâm Dự báo khí tượng thủy văn quốc gia, đợt không khí lạnh đầu mùa sẽ ảnh hưởng đến "
        "miền Bắc từ đêm 10/10. Nhiệt độ thấp nhất ở Hà Nội có thể xuống 18 độ C.\n"
        "Người dân được khuyến cáo giữ ấm cơ thể khi ra đường vào sáng sớm.")
except (AIFatalError, AITemporaryError, AIArticleError) as loi:
    print(f"LỖI ({type(loi).__name__}): {loi}")
    raise SystemExit(1)
print("Tiêu đề :", ket_qua["title"])
print("Tóm tắt :", ket_qua["summary"])
print("Nội dung:", ket_qua["content"])
print("Token   :", ket_qua["input_tokens"], "vào /", ket_qua["output_tokens"], "ra")