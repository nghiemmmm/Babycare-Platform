# Kế hoạch Triển khai Chi tiết từng Giai đoạn (Actionable Project Planner)

Tài liệu này chi tiết hóa các công việc cần thực hiện, các tệp cần sửa đổi và phương pháp kiểm thử cho từng giai đoạn trong lộ trình xây dựng BabyCare AI Agent.

---

## 📅 Giai đoạn 1: Nền tảng AI Core & Model Router

### 1.1 Hoàn thiện `app/AI_agents/core/reasoner.py`
* **Nhiệm vụ**: Xây dựng lớp gọi LLM tập trung qua thư viện bất đồng bộ.
* **Chi tiết kỹ thuật**:
  - Tải cấu hình từ `app/core/config.py` (Gemini API Key, OpenAI API Key).
  - Sử dụng thư viện `langchain-google-genai` (lớp `ChatGoogleGenerativeAI`) hoặc `google-genai` SDK để gọi model bất đồng bộ (`ainvoke`).
  - Tích hợp xử lý ngoại lệ (Exception handling): Nếu lỗi API Key hoặc bị rate limit, tự động trả về thông báo lỗi thân thiện thay vì crash hệ thống.
- [x] Code logic khởi tạo và gọi LLM bất đồng bộ trong `core/reasoner.py`.
- [x] Thêm xử lý lỗi Exception và cấu hình fallback sang model phụ.

### 1.2 Hoàn thiện `app/AI_agents/models/llm_factory.py`
* **Nhiệm vụ**: Cung cấp các model khác nhau cho các nhiệm vụ cụ thể.
- [x] Cấu hình model `gemini-1.5-flash` cho các tác vụ nhanh (Intent Classification, Entity Extraction).
- [x] Cấu hình model `gemini-1.5-pro` (hoặc `gpt-4o`) cho các tác vụ suy luận sâu (RAG Chat, Health Guideline check).
- [x] Code hàm `get_model(model_name: str)` trả về instance Model chuẩn.

### 1.3 Hoàn thiện `app/AI_agents/models/model_router.py`
- [x] Viết hàm tự động chọn model: Nếu chiều dài Prompt lớn hơn 10k tokens hoặc yêu cầu thuộc loại suy luận phức tạp (`deep_reasoning`), điều hướng sang `gemini-1.5-pro`, ngược lại dùng `gemini-1.5-flash`.

### 1.4 Thiết lập Tracing (LangSmith)
- [ ] Tạo file `.env` chứa `LANGSMITH_TRACING=true` và `LANGSMITH_API_KEY`.
- [x] Đăng ký các Model Callbacks để tự động trace các node chạy lên LangSmith Dashboard.

---

## 📅 Giai đoạn 2: Điều phối Trung tâm & State Manager

### 2.1 Định nghĩa State trong `app/AI_agents/orchestrator/state_manager.py`
* **Nhiệm vụ**: Cấu hình bộ nhớ trạng thái trung tâm của LangGraph.
- [x] Định nghĩa class `OverallState(TypedDict)` chứa:
  * `messages`: `Annotated[list[AnyMessage], operator.add]` (Lịch sử chat)
  * `baby_id`: `str` (ID em bé đang được chọn)
  * `current_user_id`: `str` (ID cha mẹ đang dùng)
  * `extracted_intent`: `str` (Ý định: chat, log, cry, nutrition, health, report)
  * `next_step`: `str` (Đồ thị tiếp theo cần chạy)
  * `error_message`: `Optional[str]` (Thông báo lỗi nếu có)

### 2.2 Hoàn thiện `app/AI_agents/orchestrator/task_planner.py`
* **Nhiệm vụ**: Phân loại ý định người dùng (Intent Classifier Node).
- [x] Thiết lập Prompt phân loại ý định người dùng thành các nhãn: `chat`, `log_activity`, `analyze_cry`, `check_health`, `check_nutrition`, `generate_report`.
- [x] Trích xuất các tham số đi kèm (ví dụ: `baby_id` nếu người dùng nhắc tên bé).

### 2.3 Thiết lập Đồ thị định tuyến trong `app/AI_agents/workflows/router_graph.py`
- [x] Khởi tạo `StateGraph(OverallState)`.
- [x] Thêm node `classify_intent` (gọi từ `task_planner.py`).
- [x] Đăng ký `add_conditional_edges` từ node `classify_intent` đến các Subgraph đích dựa trên giá trị của `extracted_intent`.
- [x] Đăng ký biên dịch `compile(checkpointer=...)`.

---

## 📅 Giai đoạn 3: Triển khai Subgraph CRUD & Voice Logging

### 3.1 Triển khai các Database Tools (`tools/implementation/`)
* **Nhiệm vụ**: Cho phép Agent tương tác trực tiếp với Firestore.
- [x] `baby_tools.py`: Bọc hàm `BabyService.get_baby_by_id` và cập nhật thông tin.
- [x] `growth_tools.py`: Bọc hàm `GrowthTrackingService.add_growth_log` và so sánh WHO.
- [x] `health_tools.py`: Bọc hàm `SymptomTracking` và kiểm tra chống chỉ định thuốc.
- [x] `nutrition_tools.py`: Bọc hàm `SolidFoodService.add_solid_food_log`.

### 3.2 Hoàn thiện `app/AI_agents/workflows/voice_logging_graph.py`
- [x] Tạo node **Entity Extraction Node**: Sử dụng LLM bóc tách văn bản nói dạng tự nhiên (Ví dụ: *"Bé ăn 100g cháo rau cải lúc 10h sáng"* thành `{"food_name": "cháo rau cải", "amount_g": 100.0, "time": "10:00"}`).
- [x] Tạo node **Write Database Node**: Nhận cấu trúc JSON vừa bóc tách, chọn Tool phù hợp (Ví dụ: `NutritionTrackingTool`) để ghi nhận vào Firestore.
- [x] Trả về tin nhắn xác nhận cho phụ huynh: *"Đã ghi nhận bé ăn 100g cháo rau cải thành công."*

### 3.3 Hoàn thiện `app/AI_agents/workflows/chat_graph.py`
- [x] Thiết lập prompt hệ thống cho Chat Agent (Trợ lý chăm sóc trẻ chuyên nghiệp).
- [x] Tự động nạp thông tin cấu hình hiện tại của bé (tuổi, cân nặng, chiều cao gần nhất) vào Prompt Context trước khi LLM trả lời để đảm bảo câu trả lời cá nhân hóa.

---

## 📅 Giai đoạn 4: Tích hợp RAG Y khoa & Chẩn đoán Tiếng khóc

### 4.1 Xây dựng RAG Pipeline trong `knowledge/`
- [x] `document_loader.py`: Viết code đọc tài liệu y văn chăm sóc trẻ dạng PDF/Text.
- [x] `text_splitter.py`: Cắt nhỏ tài liệu thành các chunk (khoảng 500-1000 ký tự) có overlap.
- [x] `vector_store.py`: Sử dụng thư viện vector (như ChromaDB hoặc FAISS) lưu trữ Embeddings của các chunk.
- [x] `retriever.py`: Viết hàm tìm kiếm các đoạn văn bản có độ tương đồng cao nhất với câu hỏi của phụ huynh.
- [x] `tools/implementation/rag_tools.py`: Đóng gói hàm retriever thành Tool.

### 4.2 Triển khai Đồ thị phân tích tiếng khóc (`workflows/cry_analysis_graph.py`)
- [x] Node **Cry Detection**: Gọi tệp `app/ai/cry_classifier.py` đã viết ở các bước trước để nhận kết quả phân loại tiếng khóc giả lập.
- [x] Node **Context Aggregator**: Đọc dữ liệu từ Firestore xem cữ bú gần nhất cách đây bao lâu, bé thức được bao lâu để bổ sung dữ liệu ngữ cảnh cho LLM.
- [x] Node **Reasoner Node**: LLM kết hợp kết quả âm thanh + ngữ cảnh sinh hoạt để đưa ra chẩn đoán xác thực nhất (Ví dụ: *Bé khóc nhãn hungry nhưng vừa bú xong 10 phút trước -> Có thể bé bị đầy hơi cần vỗ ợ hơi*).
- [x] Node **Sound Conditioning Trigger**: Tự động trả về lệnh phát tệp nhạc ru phù hợp hoặc file giọng nói mẹ ảo (`ai_voice_mom`).

---

## 📅 Giai đoạn 5: Tổng hợp Báo cáo, Lưu Checkpoint & Cổng API

### 5.1 Hoàn thiện đồ thị Báo cáo (`workflows/report_graph.py`)
- [x] Đọc toàn bộ nhật ký tuần/tháng gần nhất của bé (ăn, ngủ, thuốc, cân nặng).
- [x] Viết prompt cho LLM tổng hợp các chỉ số phát triển, đưa ra cảnh báo sức khỏe và đề xuất dinh dưỡng tuần tới.
- [x] Viết helper xuất báo cáo ra file PDF sử dụng thư viện `ReportLab`.

### 5.2 Xây dựng Custom Firestore Checkpointer (`orchestrator/state_manager.py`)
* **Nhiệm vụ**: Lưu trữ lịch sử LangGraph bền vững thay vì lưu trong bộ nhớ RAM.
- [x] Viết class `FirestoreCheckpointer` kế thừa từ `BaseCheckpointSaver` của LangGraph.
- [x] Viết logic lưu trạng thái (`put`) và đọc trạng thái (`get`) dựa trên `thread_id` vào collection `chat_checkpoints` của Firestore.

### 5.3 Mở API Gateway phục vụ ứng dụng Di động (`api/router/`)
- [x] Viết FastAPI Router tiếp nhận payload: `{"message": "...", "baby_id": "...", "thread_id": "..."}`.
- [x] Gọi `agent_orchestrator.py` để invoke Router Graph của LangGraph.
- [x] Hỗ trợ cả hai cơ chế trả về: Streaming câu trả lời (Server-Sent Events) hoặc trả về JSON đầy đủ sau khi Agent hoàn thành.

Không dùng LLM cho mọi request. Chỉ dùng model mạnh khi thực sự cần reasoning