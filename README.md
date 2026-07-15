# 🍼 BabyCare AI - Backend Services

BabyCare AI là nền tảng API Backend được xây dựng bằng **FastAPI (Python)** kết hợp với **Google Cloud Firestore (NoSQL)** và tích hợp Trí tuệ nhân tạo (AI) giúp phụ huynh chăm sóc, ghi nhận nhật ký và theo dõi sức khỏe trẻ sơ sinh một cách cá nhân hóa và thông minh.

---

## 🚀 Các Tính Năng Chính

* **Phân quyền & Đồng bộ (Caregiver Sync):** Phân quyền quản lý giữa nhiều người chăm sóc (Bố, Mẹ, Ông bà, Người giữ trẻ) trên cùng một hồ sơ bé theo thời gian thực.
* **Theo dõi Phát triển (Growth Tracking):** Ghi nhận chiều cao, cân nặng, vòng đầu và đối chiếu trực quan với các chỉ số tiêu chuẩn của Tổ chức Y tế Thế giới (WHO).
* **Nhật ký dùng thuốc (Medication Tracking):** Quản lý lịch trình, liều lượng uống thuốc và vitamin của bé nhằm tránh việc quên liều hoặc uống lặp.
* **Nhật ký Ăn dặm (Solid Food Tracking):** Ghi chép thực đơn ăn dặm, lượng ăn (gram) và phản ứng của bé (yêu thích, trớ, dị ứng...).
* **AI Cry Detection & Sound Conditioning:** Nhận diện và chẩn đoán nguyên nhân tiếng khóc của bé, tự động phát âm thanh xoa dịu (White Noise, Nhạc ru) và clone giọng mẹ ảo vỗ về bé.
* **AI Chatbot (GraphRAG):** Trợ lý ảo hỗ trợ trả lời các câu hỏi chăm sóc trẻ dựa trên cơ sở tri thức y khoa đã được xác thực.

---

## 🛠️ Công Nghệ Sử Dụng

* **Ngôn ngữ:** Python 3.11+
* **Framework:** FastAPI (Cơ chế Asynchronous, Pydantic v2 cho validation)
* **Database:** Google Cloud Firestore (NoSQL Document Database)
* **Môi trường & Package Manager:** `uv` (Công cụ quản lý môi trường ảo và thư viện siêu tốc bằng Rust)
* **Kiểm thử:** Pytest (Unit Testing & Mocks)
* **Containerization:** Docker & Docker Compose

---

## 📁 Cấu Trúc Mã Nguồn (Modular Monolith)

Dự án áp dụng cấu trúc Domain-Driven/Modular sạch sẽ, tách biệt rõ ràng các lớp trách nhiệm (Router - Service - Repository - Schema):

```text
babycare-ai/
├── app/
│   ├── core/                  # Cấu hình hệ thống, middleware, exception handler, cấu hình bảo mật
│   ├── infrastructure/        # Khởi tạo kết nối database Firestore, email, storage
│   ├── modules/               # Các mô-đun nghiệp vụ độc lập (CRUD)
│   │   ├── auth/              # Đăng ký, đăng nhập và phân quyền JWT
│   │   ├── baby/              # Quản lý hồ sơ bé và người giám hộ
│   │   ├── growth_tracking/   # Nhật ký chiều cao, cân nặng
│   │   ├── health_records/    # Nhật ký triệu chứng & hồ sơ bệnh án
│   │   ├── medication/        # Nhật ký sử dụng thuốc
│   │   ├── nutrition/         # Nhật ký ăn dặm & đề xuất dinh dưỡng
│   │   └── cry/               # Nhật ký ghi nhận tiếng khóc của bé
│   ├── ai/                    # Chứa mô hình phân loại tiếng khóc, dỗ bé tự động (Sound Conditioning)
│   ├── rag/                   # Hệ thống Chatbot thông minh (GraphRAG + LLM)
│   ├── shared/                # Các lớp Base Repository và Utilities dùng chung
│   └── main.py                # Điểm khởi chạy FastAPI Application
├── docker/                    # Dockerfile và tệp Docker Compose cấu hình chạy môi trường ảo
├── tests/                     # Unit test phân tách theo unit/ và integration/
├── seed_db.py                 # Script nạp dữ liệu mẫu khởi tạo (healthcare tips, alert rules)
├── test_db.py                 # Script kiểm tra nhanh kết nối Firebase Firestore
├── pyproject.toml             # Cấu hình dự án & linter
└── requirements.txt           # Danh sách các thư viện phụ thuộc của dự án
```

---

## 💻 Hướng Dẫn Cài Đặt & Khởi Chạy

### 1. Chuẩn Bị Môi Trường
1. Nhân bản dự án về máy:
   ```bash
   git clone <repository_url>
   cd babycare-ai
   ```
2. Tạo tệp cấu hình môi trường `.env` từ tệp mẫu:
   * Copy tệp `.env.example` thành `.env`
   * Điền đường dẫn tới tệp chứng thực Firebase Service Account (`FIREBASE_CREDENTIALS_PATH`) của bạn.

### 2. Thiết Lập Môi Trường Ảo Bằng `uv` (Khuyên dùng)
Dự án được tối ưu hóa để chạy bằng `uv` (nhanh gấp nhiều lần pip thông thường):
```powershell
# Tạo môi trường ảo
uv venv

# Kích hoạt môi trường ảo (Windows PowerShell)
.venv\Scripts\activate

# Cài đặt toàn bộ dependencies từ requirements.txt
uv pip install -r requirements.txt
```

### 3. Nạp Dữ Liệu Mẫu (Database Seeding)
Chạy script để nạp các thông tin cấu hình luật cảnh báo (`alert_rules`) và mẹo y tế (`healthcare_tips`) vào Firestore:
```bash
python seed_db.py
```

### 4. Khởi Chạy API Server
* **Bằng PowerShell script tiện ích:**
  ```powershell
  .\dev.ps1
  ```
* **Hoặc bằng lệnh trực tiếp:**
  ```bash
  fastapi dev app/main.py
  ```
Server sẽ chạy ở địa chỉ `http://localhost:8000`. 
Truy cập tài liệu API tự động tại: `http://localhost:8000/api/docs` (Swagger UI).

---

## 🧪 Chạy Kiểm Thử (Testing)

Dự án tích hợp sẵn `pytest` để chạy các unit test kiểm tra chất lượng code và validation của các Pydantic Schemas/Repositories:
```bash
pytest
```
Để kiểm tra độ bao phủ hoặc xuất báo cáo chi tiết:
```bash
pytest -v
```

---

## 🐳 Khởi Chạy Bằng Docker
Nếu bạn muốn chạy toàn bộ ứng dụng trong Docker container:
```bash
docker-compose -f docker/docker-compose.yml up --build
```
Ứng dụng sẽ tự động tải các dependencies và khởi chạy ở cổng `8000`.
