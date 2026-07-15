# 🍼 BabyCare AI - Tài liệu Hệ thống (System Documentation)

## Tổng quan

BabyCare AI là nền tảng ứng dụng AI hỗ trợ phụ huynh chăm sóc, ghi nhận nhật ký và theo dõi sức khỏe trẻ sơ sinh theo cách cá nhân hóa.

---

## Danh sách Chức năng chính

### 1. Authentication & User Management
* Đăng ký, đăng nhập tài khoản phụ huynh.
* Đổi mật khẩu, khôi phục mật khẩu qua email.
* JWT Authentication phục vụ bảo mật kết nối API.
* Quản lý thông tin hồ sơ cá nhân của phụ huynh.

### 2. Baby Profile & Caregiver Sync
* Quản lý thông tin cơ bản của bé: Họ tên, ngày sinh, giới tính, nhóm máu, tiền sử bệnh án, ghi chú y khoa.
* Hỗ trợ quản lý đồng thời nhiều hồ sơ bé trong cùng một tài khoản.
* **Caregiver Sync (Đồng bộ nhiều người chăm sóc):** Phân quyền và đồng bộ hóa thời gian thực (Real-time Sync) giữa các thành viên (Bố, Mẹ, Ông bà, Người giúp trẻ) cùng chăm sóc bé.

### 3. Theo dõi Chiều cao & Cân nặng (Growth Tracking)
* Ghi chép định kỳ: Chiều cao, cân nặng, vòng đầu của bé.
* Vẽ biểu đồ tăng trưởng tự động.
* So sánh trực quan chỉ số phát triển của bé với chuẩn chuẩn mực của Tổ chức Y tế Thế giới (WHO).

### 4. Hồ sơ Sức khỏe & Triệu chứng (Symptom Tracking)
* Ghi nhận diễn biến và triệu chứng sức khỏe hàng ngày của bé (ho, sốt, nôn trớ, phát ban...).
* Lưu trữ lịch sử khám bệnh, bác sĩ điều trị và chẩn đoán y khoa.

### 5. Theo dõi sử dụng Thuốc (Medication Tracking)
* Nhật ký dùng thuốc độc lập giúp ghi nhận chi tiết tên thuốc, liều lượng, giờ cho uống và người kê đơn.
* Đánh giá hiệu quả đợt điều trị và giảm thiểu việc quên liều hoặc quá liều.

### 6. Theo dõi & Đề xuất Dinh dưỡng Ăn dặm (Nutrition & Solid Food AI)
* **Theo dõi ăn dặm:** Ghi nhận thực đơn ăn dặm, lượng ăn (gram) và phản ứng của bé (yêu thích, trớ, dị ứng...).
* **AI Recommendation:** Đề xuất thực phẩm phù hợp, thực phẩm cần tránh dựa trên tuổi, cân nặng và chiều cao của bé.

### 7. Phân tích Tiếng khóc & Vỗ về Tự động (AI Cry Detection & Sound Conditioning)
* **Dự đoán nguyên nhân tiếng khóc:** Phân tích bản thu âm tiếng khóc trực tiếp kết hợp với dữ liệu ngữ cảnh (lịch sử bú, thời gian thức, tã bẩn) để tìm nguyên nhân (đói, mệt, đau đớn, khó chịu).
* **AI Voice Mom (Mẹ ảo):** Sử dụng công nghệ nhân bản giọng nói để phát tiếng nói vỗ về ấm áp của mẹ khi bé khóc.
* **Automated Sound Conditioning:** Tự động phát âm thanh thích hợp (Tiếng ồn trắng, Tiếng ồn hồng, Nhạc ru) để xoa dịu giúp bé tự ngủ lại.
* Thu thập phản hồi độ chính xác từ phụ huynh để cải thiện mô hình AI.

### 8. AI Chatbot (GraphRAG + LLM)
* Chatbot tư vấn giải đáp nhanh các thắc mắc thường gặp của phụ huynh về giấc ngủ, dinh dưỡng, cách cho bú, và xử trí các dấu hiệu bất thường.
* Sử dụng công nghệ **GraphRAG** để truy xuất thông tin chính xác từ cơ sở tri thức y khoa uy tín.
* Cá nhân hóa câu trả lời dựa trên hồ sơ sức khỏe thực tế của bé.

### 9. Hệ thống Nhắc nhở & Thông báo (Reminder & Notification)
* Gửi thông báo nhắc lịch khám bệnh định kỳ.
* Cảnh báo sức khỏe sớm từ AI (cảnh báo sốt cao kéo dài, ngủ bất thường, hoặc sụt giảm lượng bú đột ngột).

### 10. Cơ sở Tri thức Y khoa (Medical Knowledge Base)
* Lưu trữ và tra cứu các bài viết y khoa được kiểm duyệt về cách chăm sóc trẻ sơ sinh.
* Làm nguồn dữ liệu nền tảng cho hệ thống GraphRAG.

### 11. Quản lý Dữ liệu Huấn luyện AI (Dataset Management)
* Quản lý bộ dữ liệu âm thanh tiếng khóc (ví dụ: Donate-a-Cry Corpus) dùng để huấn luyện và kiểm thử mô hình dự đoán.

---

## Kiến trúc Chức năng (System Architecture Tree)

```text
BabyCare AI
├── Authentication & User Management
├── Baby Profile & Caregiver Sync
├── Growth Tracking
├── Symptom Tracking (Health Records)
├── Medication Tracking
├── Nutrition & Solid Food AI
├── AI Cry Detection & Sound Conditioning
├── AI Chatbot (GraphRAG + LLM)
├── Reminder & Notification System
├── Medical Knowledge Base
└── Dataset Management
```

