# 🍼 BabyCare AI - Nền Tảng Chăm Sóc Trẻ Sơ Sinh Thông Minh

BabyCare AI là một nền tảng ứng dụng toàn diện (Full-Stack) được thiết kế nhằm giúp cha mẹ dễ dàng ghi chép nhật ký, theo dõi sức khỏe và nhận diện tiếng khóc của trẻ sơ sinh bằng trí tuệ nhân tạo (AI). 

Dự án tích hợp đầy đủ giao diện người dùng **React (TypeScript)** mượt mà, máy chủ trung gian **Node.js Express Proxy**, và API dịch vụ **FastAPI (Python)** kết nối trực tiếp với **Google Cloud Firestore**.

---

## 🚀 Các Tính Năng Bản Địa Hóa & Nổi Bật Hiện Tại

* **Giao Diện Tiếng Việt Toàn Diện (UI Localization):** 100% các trang và nhãn chức năng (Dashboard, Dinh dưỡng, Tăng trưởng, Sức khỏe, Phòng chat AI, Hồ sơ) đã được Việt hóa chỉn chu, có tính thẩm mỹ và thân thiện với người dùng Việt.
* **Lưu Trữ Ảnh Em Bé Cục Bộ (Local Static Assets):** Không còn tải ảnh đại diện từ các liên kết Unsplash bên ngoài. Ảnh đại diện của bé Leo và bé Bo được tạo trực tiếp bằng AI và phục vụ trực tiếp thông qua thư mục tĩnh cục bộ [app/static/img](file:///d:/ViT/BABYCARE/babycare-ai/app/static/img).
* **Phân Tích Bách Phân Vị WHO Chuẩn:** Tự động tính toán bách phân vị về cân nặng, chiều cao và vòng đầu của trẻ theo biểu đồ tăng trưởng tiêu chuẩn thế giới của WHO.
* **Cảnh Báo An Toàn Dùng Thuốc (Paracetamol Safety):** Cơ chế khóa nút và đếm ngược thời gian an toàn tự động (tối thiểu cách nhau 4 tiếng cho mỗi liều Paracetamol/Hapacol) để bảo vệ sức khỏe và lá gan của trẻ nhỏ.
* **AI Chatbot & Phục Hồi Lịch Sử Trò Chuyện:** Trợ lý ảo tư vấn nhi khoa sử dụng Gemini Flash và đồ thị LangGraph orchestrator. Tin nhắn trò chuyện được tự động đồng bộ và nạp lại trực tiếp từ Firestore Checkpointer của LangGraph khi chuyển đổi phiên chat.
* **Trích Xuất Nhật Ký Thông Minh (Smart Log Extraction):** Chatbot AI tự động nhận biết thông tin ăn uống (ví dụ: *"Bé uống 180ml sữa công thức lúc 10:30 SA"*) để xuất ra thẻ lưu nhanh giúp cha mẹ rảnh tay hơn.
* **Bấm Giờ Giấc Ngủ (Sleep Timer):** Đo lường chi tiết giờ giấc ngủ của bé và lưu trữ nhật ký tự động.

---

## 📁 Cấu Trúc Mã Nguồn Workspace

```text
babycare-ai/
├── app/                        # 🐍 BACKEND LAYER (FastAPI)
│   ├── core/                   # Cấu hình hệ thống, middleware, exception handler
│   ├── infrastructure/         # Khởi tạo kết nối Firestore database
│   ├── modules/                # Các mô-đun nghiệp vụ độc lập
│   │   ├── auth/               # Đăng nhập giả lập & xác thực người dùng
│   │   ├── baby/               # Quản lý hồ sơ bé và người giám hộ
│   │   ├── growth_tracking/    # Nhật ký số đo chiều cao, cân nặng & bách phân vị WHO
│   │   ├── health_records/     # Nhật ký triệu chứng & hồ sơ bệnh án
│   │   ├── medication/         # Nhật ký và bộ kiểm soát an toàn dùng thuốc
│   │   ├── nutrition/          # Ghi nhận cữ bú sữa, ăn dặm & nguyên liệu dị ứng
│   │   └── cry/                # Phân tích âm thanh tiếng khóc của trẻ
│   ├── static/                 # Phục vụ file tĩnh (chứa ảnh avatar em bé cục bộ)
│   │   └── img/                # Thư mục lưu trữ leo.png và bo.png
│   └── main.py                 # Điểm khởi chạy FastAPI chính (Mounter StaticFiles)
│
├── frontend/                   # ⚛️ FRONTEND LAYER (React + Vite + TypeScript)
│   ├── src/
│   │   ├── components/         # Các View giao diện đã Việt hóa (DashboardView, GrowthView, NutritionView...)
│   │   ├── App.tsx             # Hợp nhất định tuyến, giao diện chính và nạp dữ liệu từ backend
│   │   ├── data.ts             # Bộ mock dữ liệu khởi tạo bằng tiếng Việt và ảnh tĩnh cục bộ
│   │   └── types.ts            # Định nghĩa các kiểu dữ liệu dùng trong dự án
│   ├── server.ts               # Máy chủ Express Proxy trung gian (cổng 3000), định tuyến /api và /static
│   ├── vite.config.ts          # Cấu hình xây dựng Vite
│   └── package.json            # Thư viện phụ thuộc của React và các lệnh script chạy dev
│
├── scripts/                    # 🧪 KỊCH BẢN KIỂM THỬ VÀ ĐỒNG BỘ API
│   ├── seed_demo_data.py       # Nạp cơ sở dữ liệu mẫu tiếng Việt vào Firestore cho bé Leo
│   ├── update_db_avatar.py     # Cập nhật đường dẫn avatar của em bé trong Firestore sang ảnh tĩnh cục bộ
│   ├── test_baby_api.py        # Kiểm thử các API tạo, đọc, sửa, xóa hồ sơ em bé
│   ├── test_dashboard_api.py   # Kiểm thử API tổng hợp dữ liệu màn hình Dashboard chính
│   ├── test_health_api.py      # Kiểm thử quy tắc cảnh báo nguy cấp 4 tiếng dùng thuốc
│   ├── test_logs_api.py        # Kiểm thử API lưu triệu chứng bệnh án & bệnh trạng nhật ký
│   ├── test_nutrition_api.py   # Kiểm thử API cữ ăn sữa, ăn dặm & thử dị ứng nguyên liệu
│   └── test_ai_chat_api.py     # Kiểm thử luồng chat AI LangGraph & trích xuất log tự động
```

---

## 💻 Hướng Dẫn Cài Đặt & Khởi Chạy

### 1. Chuẩn Bị Môi Trường Backend & Nạp Dữ Liệu
1. Tạo môi trường ảo Python và kích hoạt:
   ```bash
   python -m venv venv
   # Kích hoạt trên Windows PowerShell:
   .\venv\Scripts\activate
   ```
2. Cài đặt các thư viện phụ thuộc:
   ```bash
   pip install -r requirements.txt
   ```
3. Tạo tệp `.env` ở thư mục gốc và điền mã khóa API Gemini của bạn để sử dụng chatbot:
   ```env
   GEMINI_API_KEY=AIzaSy...
   ```
4. Khởi chạy máy chủ Backend (FastAPI):
   ```bash
   fastapi dev app/main.py
   ```
   *Backend sẽ chạy tại: `http://localhost:8000`*

5. Nạp dữ liệu mẫu Tiếng Việt ban đầu & Cập nhật ảnh đại diện em bé:
   ```bash
   # Nạp dữ liệu cữ ăn, số đo và thuốc mẫu
   python scripts/seed_demo_data.py
   # Cập nhật liên kết avatar Firestore sang thư mục tĩnh cục bộ
   python scripts/update_db_avatar.py
   ```

### 2. Chuẩn Bị Môi Trường Frontend & Khởi Chạy
1. Di chuyển vào thư mục frontend:
   ```bash
   cd frontend
   ```
2. Cài đặt các gói phụ thuộc bằng npm hoặc yarn:
   ```bash
   npm install
   ```
3. Khởi chạy máy chủ phát triển Frontend (Node.js Express Proxy):
   ```bash
   npm run dev
   ```
   *Express Proxy và giao diện React sẽ chạy tại: `http://localhost:3000`*

Bây giờ, bạn có thể truy cập thẳng vào `http://localhost:3000` trên trình duyệt để trải nghiệm toàn bộ nền tảng chăm sóc em bé bằng Tiếng Việt cực kỳ mượt mà!

---

## 🧪 Cách Chạy Các Tập Lệnh Kiểm Chứng API Cục Bộ

Để chạy thử nghiệm và kiểm chứng độc lập tính chính xác của các API kết nối Firestore của hệ thống (trong khi server Backend vẫn đang chạy), bạn có thể chạy các tập lệnh Python sau:

```bash
# Kiểm tra API Hồ sơ em bé:
python scripts/test_baby_api.py

# Kiểm tra API Trang chủ (Dashboard):
python scripts/test_dashboard_api.py

# Kiểm tra logic An toàn dùng thuốc (Health Safety):
python scripts/test_health_api.py

# Kiểm tra nhật ký Nhật ký bệnh án (Diary/Logs):
python scripts/test_logs_api.py

# Kiểm tra cữ ăn uống & dị ứng nguyên liệu (Nutrition):
python scripts/test_nutrition_api.py

# Kiểm tra chatbot LangGraph & trích xuất log (AI Agent):
python scripts/test_ai_chat_api.py
```
