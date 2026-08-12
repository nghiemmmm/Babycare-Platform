# 🍼 BabyCare AI — Nền Tảng Chăm Sóc Trẻ Sơ Sinh Thông Minh

<p align="center">
  <img src="https://img.shields.io/badge/FastAPI-0.115-009688?style=for-the-badge&logo=fastapi" />
  <img src="https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react" />
  <img src="https://img.shields.io/badge/LangGraph-0.4-FF6F00?style=for-the-badge" />
  <img src="https://img.shields.io/badge/PyTorch-2.x-EE4C2C?style=for-the-badge&logo=pytorch" />
  <img src="https://img.shields.io/badge/Firebase-Firestore-FFCA28?style=for-the-badge&logo=firebase" />
</p>

**BabyCare AI** là nền tảng chăm sóc trẻ sơ sinh toàn diện, kết hợp trí tuệ nhân tạo (AI), đồ thị tác tử đa tác nhân (Multi-Agent LangGraph), cơ sở tri thức y khoa RAG (Hybrid Search & Re-ranking) và mô hình phân loại tiếng khóc sâu (PyTorch AST) giúp cha mẹ đồng hành cùng sự phát triển của bé yêu một cách nhẹ nhàng, khoa học và chính xác.

<p align="center">
  <img src="img/dangnhap.jpg" width="48%" alt="Màn Hình Đăng Nhập BabyCare AI" />
  <img src="img/dangky2.jpg" width="48%" alt="Màn Hình Đăng Ký BabyCare AI" />
  <br>
  <em>Giao diện Đăng nhập & Đăng ký tài khoản dịu nhẹ dành cho Phụ huynh</em>
</p>

---

## ✨ Tính Năng Nổi Bật

| Tính Năng | Mô Tả |
|---|---|
| 🔊 **Nhận Diện Tiếng Khóc AI** | Mô hình AST (Audio Spectrogram Transformer) PyTorch nhận dạng **8 loại khóc** (*Đói, Gắt ngủ, Đau bụng, Cần ợ hơi, Bẩn tã, Khó chịu, Cần bế, Giật mình*) với điểm tin cậy đa lớp % |
| 🤖 **Trợ Lý AI Đa Tác Nhân** | Orchestrator LangGraph định tuyến thông minh sang các luồng chuyên biệt: Chat tư vấn nhi khoa, Báo cáo PDF, Ghi nhận nhật ký giọng nói, Tra cứu web thời gian thực, Lọc an toàn y tế |
| 🍼 **Dinh Dưỡng & Ăn Dặm** | Quản lý cữ bú (ml sữa mẹ/công thức), theo dõi ăn dặm, phát hiện dị ứng nguyên liệu, cảnh báo thực phẩm cấm theo độ tuổi (WHO/AAP) |
| 📈 **Tăng Trưởng Chuẩn WHO** | Lưu trữ và tự động tính bách phân vị cân nặng, chiều cao, vòng đầu theo biểu đồ WHO chuẩn quốc tế |
| 🏥 **Nhắc Nhở & Nhật Ký Sức Khỏe** | Ghi nhận triệu chứng, nhật ký bệnh trạng; tự động nhắc nhở và đếm ngược an toàn liều hạ sốt Paracetamol (≥ 4-6 tiếng/liều) |
| 📊 **Xuất Báo Cáo PDF** | AI tổng hợp toàn bộ dữ liệu tăng trưởng, dinh dưỡng và sức khỏe thành báo cáo PDF y khoa chuyên nghiệp |
| 🎤 **Nhật Ký Giọng Nói** | Bóc tách nhật ký ăn uống/sức khỏe từ giọng nói của cha mẹ bằng Gemini Multimodal |
| 🌐 **Tra Cứu Web Thời Gian Thực** | Tích hợp Tavily Search (fallback DuckDuckGo) khi câu hỏi vượt ngoài kho tri thức nội bộ |
| 👨‍👩‍👧 **Đồng Bộ Gia Đình** | Mời và phân quyền chia sẻ dữ liệu bé giữa cha, mẹ và người giám hộ |
| ⏱️ **Đo Lường Giấc Ngủ** | Theo dõi và tự động lưu trữ nhật ký giấc ngủ cho bé |

### 🎨 Giao Diện Ứng Dụng (Application UI Showcase)

<p align="center">
  <img src="img/tongquan1.jpg" width="100%" alt="Giao diện Trang Tổng Quan - Sinh hiệu Real-time & Phân Tích Tiếng Khóc AI" />
  <br>
  <em>Giao diện Dashboard: Các thẻ sinh hiệu thời gian thực (cữ bú, giấc ngủ, lượng sữa), cảnh báo lịch uống thuốc an toàn & thanh điều hướng chính</em>
</p>

<br>

<p align="center">
  <img src="img/tomgquan2.jpg" width="100%" alt="Giao diện Trang Tổng Quan - Biểu Đồ WHO & AI Insights" />
  <br>
  <em>Giao diện Dashboard: Trợ lý trò chuyện AI, Phân tích tiếng khóc AI real-time, Đánh giá mốc phát triển CDC/AAP & Tiến trình đường cong tăng trưởng chuẩn WHO</em>
</p>

---

## 🏗️ Kiến Trúc Tổng Thể Hệ Thống (System Architecture)

<p align="center">
  <img src="img/system-architecture (2).png" width="100%" alt="Sơ Đồ Kiến Trúc Hệ Thống BabyCare AI Platform" />
  <br>
  <em>Sơ đồ Kiến trúc Tổng thể Hệ thống BabyCare AI Platform (Frontend Next.js/React, Nginx API Gateway, Backend FastAPI, LangGraph Multi-Agent, PyTorch AST & Firestore)</em>
</p>

<br>

### 🧩 Phân Tích Các Tầng Trong Kiến Trúc

1. **Giao diện Người dùng & Cổng kết nối (Frontend & API Gateway)**:
   - **Frontend**: Được xây dựng trên nền **Next.js / React**, cung cấp giao diện phản hồi thời gian thực qua WebSocket/SSE, bao gồm các màn hình chính: *Trò chuyện AI, Dashboard tổng quan, Phân tích tiếng khóc, Theo dõi tăng trưởng, Kế hoạch dinh dưỡng, Xuất báo cáo & Cài đặt*.
   - **NGINX API Gateway**: Đảm nhận Reverse Proxy, SSL Termination, Load Balancing, Rate Limiting và bảo mật hệ thống.

2. **Tầng Ứng Dụng & Dịch Vụ Nghiệp Vụ (FastAPI Layer)**:
   - **Authentication Service**: Quản lý xác thực an toàn qua **JWT / OAuth2**, quản lý phiên đăng nhập và phân quyền gia đình (RBAC).
   - **Business API Services**: Xử lý các logic nghiệp vụ như *Hồ sơ bé, Nhật ký tăng trưởng, An toàn thuốc & sức khỏe, Kế hoạch cữ sữa/ăn dặm, Hoạt động giấc ngủ, Xuất file báo cáo PDF và Thông báo*.

3. **Tầng Điều Phối Đa Tác Nhân AI (LangGraph Multi-Agent Orchestrator)**:
   - **Intent Classification (TaskPlanner)**: Phân tích mục đích của phụ huynh để điều hướng chính xác.
   - **7 Subgraphs Chuyên Biệt**: *ChatGraph* (RAG Nhi khoa), *VoiceLogging* (Gemini Multimodal bóc tách giọng nói), *CryAnalysis* (Suy luận nguyên nhân khóc), *HealthGraph* (An toàn liều thuốc & lịch sử sức khỏe), *NutritionGraph* (Thực đơn & lọc dị ứng), *ReportGraph* (Xuất báo cáo PDF), *OutOfScopeGraph* (Tra cứu web thời gian thực).
   - **Human-in-the-Loop Checkpoint**: Tạm dừng kiểm duyệt và duyệt kết quả trước khi đưa ra phản hồi tổng hợp cuối cùng.

4. **Pipeline Chuyên Chế Xử Lý Tiếng Khóc & Giọng Nói (Specialized Pipelines)**:
   - **Cry Analysis Pipeline (PyTorch AST)**: Nạp âm thanh (.wav/.mp3) → Trích xuất đặc trưng Kaldi Feature Extraction → Mô hình **AST Transformer (PyTorch)** → Dự đoán 8 loại khóc → Gợi ý nhạc ru & tiếng ồn trắng dỗ bé.
   - **Voice Understanding Pipeline**: Thu âm giọng nói → Gemini Multimodal → Bóc tách nhật ký hoạt động → Đưa vào dữ liệu ghi nhận chuẩn hóa cho bé.

5. **Tầng Lưu Trữ & Dịch Vụ Phụ Trợ (Data Stores & External Services)**:
   - **Firestore (NoSQL)**: Lưu trữ hồ sơ bé, dữ liệu tăng trưởng, nhật ký sức khỏe & cữ bú thời gian thực.
   - **Vector Database (FAISS)**: Kho lưu trữ tri thức y khoa nhi khoa, cẩm nang WHO/AAP & dữ liệu dị ứng.
   - **Redis Cache & Queue**: Bộ đệm tăng tốc độ phản hồi và hàng chờ xử lý tác vụ background.
   - **Dịch vụ tích hợp ngoài**: Gemini API, Tavily/DuckDuckGo Search, Cloudinary Media Storage, Firebase Auth.

---

## 📁 Cấu Trúc Mã Nguồn

```text
babycare-ai/
├── img/                              # 🖼️ HÌNH ẢNH KIẾN TRÚC & GIAO DIỆN HỆ THỐNG
│   ├── dangnhap.jpg                  # Màn hình Đăng nhập
│   ├── dangky2.jpg                   # Màn hình Đăng ký
│   ├── tongquan1.jpg                 # Dashboard phần 1 (Sinh hiệu & Nhắc nhở)
│   ├── tomgquan2.jpg                 # Dashboard phần 2 (AI Chat & Biểu đồ WHO)
│   ├── system-architecture (2).png   # Sơ đồ Kiến trúc Tổng thể Hệ thống
│   ├── multi-agent-system-architecture.png # Sơ đồ Kiến trúc Multi-Agent LangGraph
│   ├── ingestion.png                 # Sơ đồ RAG Ingestion Pipeline
│   └── retrival.png                  # Sơ đồ RAG Hybrid Retrieval & Re-ranking
│
├── app/                              # 🐍 BACKEND LAYER (FastAPI)
│   ├── core/                         # Cấu hình, middleware, lifespan, email service
│   ├── infrastructure/               # Khởi tạo kết nối Firestore & Redis
│   ├── modules/                      # Các module nghiệp vụ RESTful API
│   │   ├── auth/                     # Xác thực JWT & quản lý người dùng
│   │   ├── baby/                     # Hồ sơ em bé (CRUD)
│   │   ├── growth_tracking/          # Tăng trưởng & bách phân vị WHO
│   │   ├── health_records/           # Nhật ký bệnh trạng & triệu chứng sức khỏe
│   │   ├── nutrition/                # Cữ bú, ăn dặm, dị ứng & hướng dẫn WHO/AAP
│   │   ├── cry/                      # Upload & phân tích tiếng khóc AI
│   │   ├── guardian/                 # Người giám hộ & phân quyền gia đình
│   │   └── ai_agent/                 # Chat AI, giọng nói, báo cáo & sleep timer
│   ├── AI_agents/                    # 🤖 MULTI-AGENT AI LAYER (LangGraph)
│   │   ├── orchestrator/             # Agent Orchestrator + State Manager + Task Planner
│   │   ├── workflows/                # Đồ thị tác nhân (Chat, Report, Voice, CryAnalysis, OutOfScope)
│   │   ├── agents/                   # Các tác nhân chuyên biệt (Health, Nutrition, Voice, Cry)
│   │   ├── tools/                    # Công cụ: WebSearch (Tavily/DuckDuckGo), RAG, CryTools
│   │   ├── memory/                   # Bộ nhớ ngữ nghĩa HuggingFace + FAISS
│   │   ├── knowledge/                # Cơ sở tri thức nhi khoa RAG (FAISS vector store + BM25)
│   │   ├── prompts/                  # Hệ thống prompt chuyên biệt cho từng tác nhân
│   │   ├── core/                     # Hằng số, mô hình suy luận (Gemini Pro/Flash, Provider Router)
│   │   └── utils/                    # Các tiện ích hỗ trợ
│   ├── ai/                           # 🔊 ML INFERENCE LAYER (PyTorch)
│   │   ├── CRY/                      # Mô hình AST nhận dạng tiếng khóc
│   │   │   ├── inference.py          # Trích xuất đặc trưng Kaldi fbank + suy luận AST
│   │   │   ├── models/ast_models.py  # Kiến trúc Audio Spectrogram Transformer
│   │   │   ├── data/                 # Nhãn phân loại (esc_class_labels_indices.csv)
│   │   │   └── weights/              # ⚠️ best_audio_model.pth (333 MB — không push Git)
│   │   ├── cry_detection/            # Tiền xử lý âm thanh & ánh xạ nhãn khóc → nhạc dỗ
│   │   └── voice_clone/              # Nhân bản giọng nói dỗ bé
│   └── static/                       # File tĩnh phục vụ qua /static
│       ├── img/                      # Avatar em bé (leo.png, bo.png)
│       ├── cry/                      # File âm thanh upload (*.gitkeep)
│       ├── reports/                  # Báo cáo PDF xuất bản (*.gitkeep)
│       ├── sounds/                   # Nhạc ru & tiếng ồn trắng dỗ bé
│       ├── samples/                  # Âm thanh mẫu kiểm thử
│       └── voices/                   # Giọng nói nhân bản
│
├── frontend/                         # ⚛️ FRONTEND LAYER (React + Vite + TypeScript)
│   ├── src/
│   │   ├── components/               # Các View đã Việt hóa mượt mà
│   │   │   ├── DashboardView.tsx     # Tổng quan + Phân tích tiếng khóc AI
│   │   │   ├── AiHubView.tsx         # Phòng Chat AI + Upload file
│   │   │   ├── NutritionView.tsx     # Dinh dưỡng, dị ứng & cẩm nang an toàn
│   │   │   ├── GrowthView.tsx        # Biểu đồ tăng trưởng WHO
│   │   │   ├── HealthView.tsx        # Nhắc nhở sức khỏe & nhật ký liều thuốc
│   │   │   ├── LogsView.tsx          # Nhật ký tổng hợp
│   │   │   └── ProfileView.tsx       # Hồ sơ em bé & người giám hộ
│   │   ├── App.tsx                   # Điều phối routing & trạng thái toàn cục
│   │   ├── types.ts                  # Định nghĩa kiểu dữ liệu TypeScript
│   │   └── data.ts                   # Dữ liệu mẫu khởi tạo
│   └── package.json
│
├── tests/
│   └── unit/
│       └── test_ai_core.py           # 21 unit test tự động (AI Core, Memory, Tools)
│
├── scripts/                          # Công cụ seed & kiểm thử thủ công
├── requirements.txt                  # Phụ thuộc Python
├── .env.example                      # Mẫu biến môi trường
├── .gitignore                        # Bỏ qua model weights, uploads, secrets
└── pyproject.toml                    # Cấu hình pytest
```

---

## 🚀 Hướng Dẫn Cài Đặt & Khởi Chạy

### Yêu Cầu Hệ Thống

- Python **3.11+**
- Node.js **18+**
- Tài khoản **Google Firebase** (Firestore)
- API Key **Google Gemini** (bắt buộc)
- API Key **Tavily** (tuỳ chọn — tự động fallback DuckDuckGo)

### 1. Cài Đặt Backend

```bash
# Tạo và kích hoạt môi trường ảo Python
python -m venv venv
.\venv\Scripts\activate        # Windows PowerShell
# source venv/bin/activate     # macOS / Linux

# Cài đặt phụ thuộc
pip install -r requirements.txt
```

### 2. Cấu Hình Biến Môi Trường

Tạo file `.env` tại thư mục gốc từ file mẫu:

```bash
cp .env.example .env
```

Điền các giá trị vào `.env`:

```env
# Google Gemini AI
GEMINI_API_KEY=AIzaSy...

# Firebase Admin SDK
FIREBASE_CREDENTIALS_PATH=path/to/firebase-adminsdk.json

# Tavily Web Search (tuỳ chọn)
TAVILY_API_KEY=tvly-...
```

### 3. Tải Model Trọng Số AI Tiếng Khóc

> ⚠️ File trọng số `best_audio_model.pth` (333 MB) **không được push lên Git** do giới hạn kích thước.
> Tải thủ công và đặt vào đúng thư mục:

```bash
app/ai/CRY/weights/best_audio_model.pth
```

### 4. Khởi Chạy Backend (FastAPI)

```bash
fastapi dev app/main.py
# Backend: http://localhost:8000
# Swagger UI: http://localhost:8000/docs
```

### 5. Khởi Chạy Frontend (React + Vite)

```bash
cd frontend
npm install
npm run dev
# Frontend: http://localhost:5173
```

---

## 🧪 Kiểm Thử Tự Động & Đánh Giá AI (Evaluation Benchmark)

### 1. Unit Tests Hệ Thống

```bash
# Chạy toàn bộ 21 unit test tự động (AI Core, Memory, Tools)
.\venv\Scripts\python.exe -m pytest tests/unit/test_ai_core.py -v

# Kết quả: 21 passed (100% thành công)
```

### 2. Chỉ Số Đánh Giá Bộ Truy Xuất RAG Y Khoa (MedicalRetriever Evaluation)

Báo cáo kiểm định chất lượng tự động của **MedicalRetriever (FAISS + BAAI/bge-m3)** trên tập dữ liệu chuẩn Golden Dataset (`tests/evaluation/local_retriever_report.md`):

| Chỉ số Đánh Giá | Giá trị Trung bình | Mô tả Chi tiết |
| :--- | :---: | :--- |
| 🎯 **Mean Hit@3** | **`1.00` (100%)** | Tỷ lệ tìm thấy tài liệu y tế chuẩn trong Top 3 kết quả |
| 🎯 **Mean Hit@5** | **`1.00` (100%)** | Tỷ lệ tìm thấy tài liệu y tế chuẩn trong Top 5 kết quả |
| 🏆 **MRR (Mean Reciprocal Rank)** | **`0.92` (92%)** | Thứ hạng vị trí đúng trung bình trong kết quả tìm kiếm |
| 🥇 **Mean Hit@1** | **`0.83` (83%)** | Tỷ lệ tìm thấy đúng ngay vị trí đầu tiên (#1) |

#### 📝 Kết Quả Kiểm Thử Thực Tế Theo Các Kịch Bản Nhi Khoa Tiêu Biểu

| STT | Kịch Bản Y Tế Phụ Huynh Hỏi | Từ Khóa Y Khoa Mong Đợi | Hit@1 | Hit@3 | Hit@5 | MRR |
| :---: | :--- | :--- | :---: | :---: | :---: | :---: |
| 1 | *Lời khuyên rèn bé sơ sinh tự ngủ* | `['quấy khóc', 'tự ngủ', 'buồn ngủ']` | **1.00** | **1.00** | **1.00** | **1.00** |
| 2 | *Bé mấy tháng tuổi tập ngồi được* | `['phát triển', 'tháng', 'tập ngồi']` | **1.00** | **1.00** | **1.00** | **1.00** |
| 3 | *Bé sốt nóng đầu 38.8 độ C làm sao* | `['sốt', 'Hapacol', 'nhiệt độ', 'Paracetamol']` | **1.00** | **1.00** | **1.00** | **1.00** |
| 4 | *Uống Hapacol 150mg 8h, 11h sốt lại có uống tiếp được không* | `['Hapacol', 'Paracetamol', 'liều', 'tiếng']` | **1.00** | **1.00** | **1.00** | **1.00** |
| 5 | *Thực đơn ăn dặm tuần đầu tiên* | `['ăn dặm', 'cháo rây', 'thực đơn', 'nhóm']` | **1.00** | **1.00** | **1.00** | **1.00** |

---

## 🤖 Kiến Trúc Đa Agent — Phân Tích Chi Tiết (Multi-Agent System Architecture)

<p align="center">
  <img src="img/multi-agent-system-architecture.png" width="100%" alt="Sơ Đồ Kiến Trúc Đa Agent Multi-Agent System Architecture" />
  <br>
  <em>Sơ đồ Kiến trúc Chi tiết Đồ thị Đa Tác nhân (Multi-Agent System Architecture) & Các Subgraph Chuyên Biệt</em>
</p>

<br>

### ⚙️ Các Thành Phần Cốt Lõi Trong Đồ Thị Đa Tác Nhân:

1. **Deterministic Bypass (Đường Tắt Định Tính)**:
   - Khi phụ huynh thực hiện các tác vụ tra cứu thông thường (xem Dashboard, kiểm tra giờ bú gần nhất, lịch uống thuốc), hệ thống kích hoạt **Deterministic Bypass** để lấy dữ liệu trực tiếp từ **Google Firestore DB** trong **~15ms** với **chi phí 0$ LLM** (tiết kiệm ~65% chi phí gọi mô hình ngôn ngữ).

2. **Routing & Dispatching Layer (Tầng Phân Luồng & Định Tuyến)**:
   - **Capability Registry & Rule Engine**: Phân loại mục đích (Intent Classification) và ánh xạ năng lực xử lý tương ứng.
   - **Model Router (Dynamic LLM Routing)**: Đánh giá độ phức tạp của câu hỏi để tự động chọn mô hình ngôn ngữ phù hợp nhằm tối ưu hiệu năng và kiểm soát chi phí.

3. **LLM Execution Engine (Động Cơ Thực Thi LLM)**:
   - **Gemini 1.5 Flash**: Đảm nhận các tác vụ phản hồi nhanh, giao tiếp giọng nói và bóc tách dữ liệu với độ trễ thấp và chi phí tối ưu.
   - **Gemini 1.5 Pro**: Đảm nhận lập luận RAG y khoa phức tạp, phân tích triệu chứng sâu và tổng hợp báo cáo.

4. **Stateful Multi-Agent Subgraphs (Các Đồ Thị Con Theo Trạng Thái)**:
   - 🏥 **HealthAgent**: Theo dõi sốt, liều dùng Paracetamol an toàn (giữ khoảng cách 4-6h), kiểm tra tiền sử dị ứng và lưu nhật ký theo dõi sức khỏe cho bé.
   - 🥑 **NutritionAgent**: Quản lý cữ bú, thiết kế thực đơn ăn dặm theo bách phân vị WHO và tự động cảnh báo nguyên liệu gây dị ứng (ví dụ: đậu nành).
   - 😭 **CryAnalysisGraph**: Kết hợp mô hình nhận dạng phổ âm thanh với ký ức cữ bú/ngủ gần nhất để đưa ra lý do bé khóc dịu dàng và đề xuất nhạc ru.
   - 🎤 **VoiceLoggingAgent**: Bóc tách nhật ký giọng nói từ phụ huynh thành dữ liệu cấu trúc chuẩn hóa cho bé.
   - 🌐 **OutOfScopeGraph**: Tìm kiếm web thời gian thực khi thông tin nằm ngoài cơ sở tri thức nội bộ với luồng Interrupted Stream.

5. **Memory & Checkpoint Persistence Layer (Tầng Bộ Nhớ & Lưu Trữ Trạng Thái)**:
   - **Short-Term Memory (MemoryManager)**: Quản lý cửa sổ hội thoại (Conversation Buffer) và Token Pruning ($\le 4000$ tokens).
   - **Long-Term Checkpointer (FirestoreCheckpointer)**: Lưu trữ trạng thái đồ thị LangGraph bền vững (Persistent Threads), cho phép phục hồi và tiếp tục hội thoại tại bất kỳ thời điểm nào.

6. **Hybrid RAG & Context Compactor Layer**:
   - Kết hợp **Dense Retriever (FAISS + BGE-M3)** và **Sparse Retriever (BM25)** qua thuật toán **RRF Merge (Reciprocal Rank Fusion)**. Sau đó, **Context Compactor (CrossEncoder Reranker `mxbai-rerank-xsmall`)** lọc nhiễu, nén ngữ cảnh và chọn Top-K đoạn văn tối ưu nhất cho LLM.

7. **Response Formatter (Định Dạng Phản Hồi)**:
   - Trích dẫn nguồn tài liệu y khoa rõ ràng (*Citation & Markdown Formatter*), phản hồi cấu trúc Rich Text chuẩn **văn phong Nhi khoa ấm áp, tinh tế và an toàn cho phụ huynh**.

---

## 🧠 Kiến Trúc RAG 2 Giai Đoạn (RAG Pipeline Analysis)

Hệ thống RAG (Retrieval-Augmented Generation) y khoa được thiết kế theo chuẩn 2 giai đoạn: **Ingestion Pipeline** (Nạp & chỉ mục) và **Retrieval Engine** (Truy xuất & Re-ranking).

---

### 📥 Giai Đoạn 1: Ingestion Pipeline — Quy Trình Nạp & Xây Dựng Chỉ Mục

<p align="center">
  <img src="img/ingestion.png" width="100%" alt="Sơ Đồ Giai Đoạn 1 - RAG Ingestion Pipeline" />
  <br>
  <em>Sơ đồ Chi tiết Quy trình Nạp, Làm giàu Ngữ cảnh và Xây dựng Chỉ mục Hybrid Search (RAG Ingestion Pipeline)</em>
</p>

<br>

#### Các Bước Thực Thi Trong Pipeline Ingestion:

1. **Document Sources (Nguồn Tài Liệu)**: Tiếp nhận đa dạng định dạng tài liệu y khoa nhi khoa (*PDF, DOCX, HTML, Markdown, JSONL, Images*).
2. **Document Parsing / OCR**: Sử dụng `PyMuPDF` / `pdfplumber` cho file PDF chuẩn, tích hợp OCR/VLM cho tài liệu quét và hình ảnh, cùng bộ phân tích HTML/Markdown.
3. **Cleaning & Normalization (Làm Sạch & Chuẩn Hóa)**: Loại bỏ nhiễu, sửa lỗi OCR, chuẩn hóa Unicode, khôi phục cấu trúc văn bản và lọc nội dung trùng lặp.
4. **Sentence-Aware Chunking (Phân Chunk Nhận Biết Câu)**: Kết hợp *Section-aware Chunking*, *Semantic Chunking* và *Sliding Window Overlap* để đảm bảo câu chữ không bị đứt đoạn giữa chừng.
5. **Contextual Enrichment (Làm Giàu Ngữ Cảnh)**: Tự động bổ sung Tiêu đề đoạn/chương, Keyword chính, Tóm tắt do LLM tạo, Mô tả ngữ cảnh và Metadata (trang, nguồn, năm, chủ đề).
6. **Xử Lý Song Song (Dual Pipeline)**:
   - **6A. Embedding Generation**: Sử dụng mô hình `BAAI/bge-m3` tạo vector embedding 1024 chiều.
   - **6B. Keyword Processing**: Tokenization, loại bỏ Stopwords và chuẩn hóa tiếng Việt cho BM25.
7. **Xây Dựng Chỉ Mục Đôi (Dual Indexing)**:
   - **7A. Vector Index**: Lưu trữ vector trong **FAISS Index** cho truy xuất ngữ nghĩa (Dense Retrieval).
   - **7B. BM25 Index**: Lưu trữ bảng chỉ mục tần suất từ trong **BM25 Index** cho truy xuất từ khóa (Sparse Retrieval).
8. **Hybrid Retrieval Index**: Hợp nhất hai chỉ mục thành bộ lưu trữ chỉ mục lai sẵn sàng phục vụ truy xuất.

---

### 🔍 Giai Đoạn 2: Retrieval Engine — Quy Trình Truy Xuất Hybrid & Re-ranking

<p align="center">
  <img src="img/retrival.png" width="100%" alt="Sơ Đồ Giai Đoạn 2 - RAG Hybrid Retrieval & Reranking Pipeline" />
  <br>
  <em>Sơ đồ Quy trình Truy xuất Lai (Hybrid Retrieval), Thuật toán Fusion RRF, CrossEncoder Re-ranking & Cơ chế Fallback An Toàn</em>
</p>

<br>

#### Các Bước Thực Thi Trong Retrieval Engine:

1. **User Query & Domain Mapping**: Tiếp nhận thắc mắc từ cha mẹ, phân loại domain y tế (*health / nutrition / general*) và chuẩn hóa truy vấn.
2. **Truy Xuất Song Song (Dense & Sparse Retrieval)**:
   - **Dense Retrieval (FAISS)**: Tìm kiếm độ tương đồng vector bằng `BAAI/bge-m3`, áp dụng Metadata Filter theo domain, lấy **Top-10 Candidate Chunks**.
   - **Sparse Retrieval (BM25)**: Trích xuất từ khóa y khoa tiếng Việt qua `SparseBM25Retriever`, lấy **Top-10 Candidate Chunks**.
3. **Reciprocal Rank Fusion (RRF)**:
   - Hợp nhất danh sách ứng viên từ Dense và Sparse.
   - Tính điểm theo công thức: $\text{RRF\_Score} = \sum \frac{1}{60 + \text{rank}_i}$
   - Khử trùng lặp nội dung dựa trên 100 ký tự đầu tiên và sắp xếp lại theo điểm RRF.
4. **CrossEncoder Re-Ranker**:
   - Sử dụng mô hình CrossEncoder **`mxbai-rerank-xsmall`** chấm điểm mức độ liên quan $[0, 1]$ cho từng cặp `(Query, Document Chunk)`.
   - Sắp xếp và trích chọn **Top-3 Document Chunks** chính xác nhất.
5. **Output Top-3 Chunks**: Chuyển giao các đoạn văn chuẩn hóa kèm trích dẫn nguồn, số trang và metadata cho LLM tổng hợp câu trả lời.
6. **Cơ Chế Dự Phòng An Toàn (Fallback Mechanism)**:
   - 🛡️ **Domain Fallback**: Nếu không tìm thấy kết quả phù hợp trong phạm vi hẹp, hệ thống tự động tìm kiếm mở rộng trên toàn bộ kho tri thức nhi khoa.
   - 🔄 **Reranker Fallback**: Trong trường hợp mô hình CrossEncoder gặp sự cố hoặc thiếu tài nguyên, hệ thống tự động chuyển sang sử dụng trực tiếp kết quả RRF Top-K.

---

## 🛠️ Bộ Công Cụ Nghiệp Vụ (Tools Registry)

| Tool | Chức năng |
|---|---|
| `baby_tools.py` | Đọc hồ sơ & chỉ số sinh học của em bé từ Firestore |
| `health_tools.py` | Tra cứu nhật ký sức khỏe, triệu chứng & nhắc nhở an toàn |
| `nutrition_tools.py` | Nhật ký cữ bú, ăn dặm & kiểm tra nguyên liệu dị ứng |
| `growth_tools.py` | Số liệu tăng trưởng & đối chiếu bách phân vị WHO |
| `cry_tools.py` | Kích hoạt suy luận phân loại tiếng khóc AST |
| `web_search_tool.py` | Tavily Search → DuckDuckGo (fallback tự động) |
| `rag_tools.py` | Tra cứu kho tri thức nhi khoa RAG (Hybrid Search) |
| `calendar_tool.py` | Tiện ích lịch & tính toán mốc thời gian |
| `email_tool.py` | Gửi email thông báo cho phụ huynh khi cần |
| `tool_registry.py` | Tự động đăng ký & quản lý tập trung tất cả công cụ |

---

## 🌐 Tổng Quan Các API Endpoint

| Method | Endpoint | Chức Năng |
|---|---|---|
| `POST` | `/api/v1/auth/login` | Đăng nhập & cấp JWT Token |
| `GET/POST` | `/api/v1/babies/` | Quản lý hồ sơ em bé |
| `POST` | `/api/v1/babies/{id}/cry-prediction` | Phân tích tiếng khóc AI (upload .wav/.mp3) |
| `GET/POST` | `/api/v1/growth/` | Nhật ký tăng trưởng & bách phân vị WHO |
| `GET/POST` | `/api/v1/health/` | Nhắc nhở sức khỏe & nhật ký liều dùng thuốc |
| `GET/POST` | `/api/v1/nutrition/feeds` | Cữ bú & ăn dặm |
| `GET` | `/api/v1/nutrition/safety-guidelines` | Cảnh báo dị ứng & thực phẩm cấm theo tuổi |
| `GET` | `/api/v1/nutrition/safety-handbook` | Cẩm nang an toàn y khoa WHO/AAP |
| `GET/POST` | `/api/v1/ai/threads` | Quản lý phiên chat AI (giới hạn 6 gần nhất) |
| `POST` | `/api/v1/ai/threads/{id}/messages` | Gửi tin nhắn & nhận phản hồi AI |
| `POST` | `/api/v1/ai/voice-extract` | Bóc tách nhật ký từ giọng nói |
| `POST` | `/api/v1/ai/reports/generate` | Tạo báo cáo PDF y khoa bằng AI |
| `GET/POST` | `/api/v1/guardians/` | Quản lý người giám hộ & phân quyền |

---

## 🔒 Bảo Mật & An Toàn Dữ Liệu

- **JWT Authentication**: Mọi endpoint đều yêu cầu Bearer token xác thực (Firebase Auth).
- **Firebase Firestore Rules**: Dữ liệu em bé được cách ly và phân quyền chặt chẽ theo `user_id`.
- **Secrets Management**: Tất cả API Key và cấu hình được quản lý tập trung qua `.env` (không push lên Git).
- **File Upload Safety**: Kiểm tra định dạng âm thanh (.wav/.mp3) và giới hạn dung lượng upload.
- **Model Weights Protection**: File trọng số `.pth` (333 MB) được loại khỏi Git qua `.gitignore`.

---

## 📜 Giấy Phép

Dự án nghiên cứu & phát triển nội bộ — **BabyCare AI Team**.
