# Yêu cầu Thiết kế Trang Trợ lý AI Chuyên sâu (AI Assistant Room)

Trang **Trợ lý AI Chuyên sâu** là trái tim của hệ thống tương tác y khoa/dinh dưỡng thông minh. Trang này cung cấp trải nghiệm hội thoại đầy đủ (Full-screen Chat) tương tự ChatGPT, tối ưu cho việc điều khiển giọng nói, phân tích tiếng khóc và trích xuất nhật ký tự động.

---

## 📸 1. Bản mẫu Thiết kế Giao diện (UI Mockup)
Dưới đây là bản vẽ giao diện phòng chat chuyên sâu của trợ lý AI BabyCare:

![Bản mẫu giao diện Trợ lý AI Chuyên sâu](C:\Users\ASUS\.gemini\antigravity-ide\brain\f22e2574-ea3e-4d3e-b65b-3248594ef5c9\ai_assistant_room_mockup_1784281438017.png)

---

## 🧱 2. Bố cục Giao diện (Page Layout)

Giao diện được phân bổ thành **3 khu vực chức năng chính**:

### ⬅️ Cột Trái: Quản lý Phòng chat (Chat Thread Sidebar)
* **Nút tạo mới**: `+ Cuộc hội thoại mới` (Tạo một `thread_id` UUID mới).
* **Danh sách phòng chat gần đây (Recent Chats)**: Lấy từ bộ sưu tập các cuộc hội thoại cũ đã lưu trong Firestore.
  - Mỗi phòng chat hiển thị tiêu đề tự động tóm tắt từ câu hỏi đầu tiên (Ví dụ: *"Tập ngồi cho bé Bo"*, *"Liều hạ sốt lúc 38.8 độ"*).
  - Có nút xóa cuộc hội thoại nhanh (Thùng rác).
* **Thông tin bé đang tương tác**: Hiển thị ảnh đại diện và tên bé đang kích hoạt hội thoại ở góc dưới sidebar.

---

### 🏛️ Cột Giữa: Khung Hội thoại Chính (Main Conversation Area)

#### 1. Header Phòng chat (Chat Header)
* Hiển thị tiêu đề phòng chat hiện tại.
* Trạng thái kết nối của Agent (Ví dụ: 🟢 *Sẵn sàng tư vấn - Powered by Gemini Flash*).
* Nút chuyển đổi nhanh bé nhận thông tin (nếu gia đình có nhiều bé).

#### 2. Luồng tin nhắn (Message Stream)
Hiển thị luồng hội thoại dạng bong bóng (Bubbles) trực quan:
* **Tin nhắn của Cha/Mẹ (Human Message)**:
  - Căn lề phải, bong bóng màu tím nhạt/xanh pastel.
  - **Trường hợp Tin nhắn giọng nói (Voice Note)**: Hiển thị một trình phát âm thanh mini kèm **sóng âm (waveform)** động. Bên dưới hiển thị văn bản đã chuyển dịch từ giọng nói (Speech-to-Text).
* **Tin nhắn của Trợ lý AI (Agent Message)**:
  - Căn lề trái, bong bóng màu trắng/kem hoặc xanh mint nhẹ mờ.
  - Trả lời bằng Markdown (hỗ trợ in đậm, gạch đầu dòng, danh sách).
  - **Hộp thông tin Nguồn tham khảo (RAG Reference Accoridon)**: Nếu câu trả lời lấy dữ liệu từ tài liệu y khoa RAG (sốt, ăn dặm), hiển thị một nút bấm nhỏ *"Xem nguồn tài liệu tham khảo"*. Khi mẹ bấm vào sẽ trổ ra tên trang sách hoặc tên tệp PDF đã tham chiếu (Ví dụ: `Nguồn: babycare_document.pdf - Trang 12`).

#### 3. Thanh nhập liệu ở cuối trang (Chat Input Box)
* **Khung gõ chữ**: Textarea tự động co giãn dòng theo chiều dài tin nhắn.
* **Nút ghi âm Microphone (Voice Record Button)**: 
  - Khi bấm và giữ (Hold to Talk) hoặc Bấm để ghi âm: Biểu tượng micro sẽ nhấp nháy đỏ kèm hiệu ứng sóng âm mờ xung quanh.
  - Khi nhả ra: Tự động gửi tệp âm thanh `.wav`/`.mp3` lên API để phân tích.
* **Nút tải tệp đính kèm (Paperclip icon)**: Cho phép đính kèm tệp âm thanh tiếng khóc của trẻ hoặc ảnh chụp bệnh lý (phát ban, màu sắc phân) gửi cho Agent phân tích.
* **Nút gửi (Send)**: Gửi tin nhắn.

---

### ➡️ Cột Phải: Bảng Trích xuất Hoạt động Thông minh (Activity Extraction Sidebar)
*Đây là tính năng độc đáo của BabyCare AI giúp cha mẹ không cần nhập form thủ công.*
* **Hoạt động**: Khi cuộc trò chuyện có chứa câu lệnh nhật ký hoạt động (Ví dụ: *"Bé vừa bú 150ml sữa..."*), cột phải sẽ tự động hiển thị một thẻ xem trước (Preview Card) cấu trúc dữ liệu vừa trích xuất được từ khung chat:
  - Thể loại: 🍼 *Ăn dặm (Feeding)*
  - Lượng ăn: `150 ml`
  - Thời gian: `12:00`
  - Ghi chú: `Sữa công thức`
* **Nút xác nhận nhanh**: Nút **`[ Xác nhận lưu vào Nhật ký ]`**. Khi phụ huynh bấm nút này, dữ liệu sẽ được lưu chính thức vào Firestore của bé mà không cần nhập lại.

---

## 💾 3. Luồng dữ liệu & API Tích hợp (API & Data Flow)

1. **Khởi tạo phòng chat**:
   - Khi chọn một phòng chat, Frontend gửi yêu cầu tải lịch sử tin nhắn của `thread_id` đó từ Firestore.
2. **Gửi tin nhắn dạng chữ**:
   - Frontend gọi: `POST /api/ai/chat` kèm body:
     ```json
     {
       "message": "Tin nhắn chữ của mẹ",
       "baby_id": "baby-123",
       "thread_id": "thread-456"
     }
     ```
3. **Gửi tin nhắn giọng nói/Tiếng khóc**:
   - Frontend ghi âm $\rightarrow$ Tải file âm thanh lên Firebase Storage và lấy đường dẫn URL.
   - Gọi API: `POST /api/ai/chat` với `"message"` là đường dẫn URL file âm thanh đó. Backend sẽ tự động phát hiện, chạy STT (Speech-to-Text) hoặc Cry Classifier để xử lý và phản hồi lại bằng văn bản dịch kèm nhận định y khoa.
