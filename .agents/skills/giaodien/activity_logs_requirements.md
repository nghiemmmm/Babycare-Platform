# Yêu cầu Thiết kế Trang Nhật ký Hoạt động (Activity Logs Page)

Trang **Nhật ký Hoạt động** cung cấp cho cha mẹ một giao diện quản lý, thống kê và điền thông tin chi tiết về mọi mặt sinh hoạt hàng ngày của bé. Dữ liệu này là đầu vào quan trọng để thuật toán RAG và AI Agent đưa ra các phân tích y khoa/dinh dưỡng cá nhân hóa.

---

## 📸 1. Bản mẫu Thiết kế Giao diện (UI Mockup)
Dưới đây là bản vẽ thiết kế giao diện trang Nhật ký sinh hoạt với các Tab phân hệ và bảng lịch sử trực quan:

![Bản mẫu giao diện Trang Nhật ký Hoạt động](C:\Users\ASUS\.gemini\antigravity-ide\brain\f22e2574-ea3e-4d3e-b65b-3248594ef5c9\activity_logs_page_mockup_1784281718161.png)

---

## 🧱 2. Bố cục & Tính năng Chi tiết (Page Sections)

Trang được thiết kế tập trung quanh **Bảng điều khiển Tab mượt mà (Tab Switcher)** gồm 3 phân hệ chính:

### 🥛 Phân hệ 1: Ăn uống (Feeding - Sữa & Ăn dặm)
* **Giao diện chính**: Bảng danh sách các bữa ăn của bé trong tuần/tháng.
* **Các trường thông tin hiển thị (Khớp `SolidFoodLogResponse`)**:
  - Tên món/Loại sữa: `food_name`
  - Lượng ăn: `amount_g` (gram/ml)
  - Phản ứng của bé: `reaction` (Hiển thị dạng Icon sinh động: 🥰 Thích, 🤢 Ghét, 🤮 Nôn trớ, 🔴 Dị ứng).
  - Thời gian: `logged_at` (Hiển thị định dạng ngày và giờ dễ đọc).
  - Ghi chú: `notes`
* **Form Thêm mới (Thủ công)**: Hộp thoại Modal hiện lên khi bấm nút `+ Thêm cữ ăn`:
  - Input text: Tên món ăn/loại sữa.
  - Input number: Lượng ăn (ml/gram).
  - Dropdown: Chọn phản ứng của bé (Like, Dislike, Vomit, Allergic).
  - Date/Time picker: Thời gian ăn.
  - Textarea: Ghi chú thêm.
* **Đường dẫn API**: 
  - Đọc lịch sử: `GET /api/nutrition/history?baby_id={baby_id}`
  - Ghi mới: `POST /api/nutrition/log?baby_id={baby_id}`
  - Xóa bản ghi: `DELETE /api/nutrition/log/{log_id}?baby_id={baby_id}`

---

### 💤 Phân hệ 2: Giấc ngủ (Sleep Tracking)
* **Giao diện chính**:
  - **Biểu đồ thanh ngang (Timeline Chart)** hiển thị các chu kỳ ngủ và thức của bé trong 24 giờ.
  - Tổng số giờ ngủ trong ngày hiển thị dạng số lớn nổi bật ở đầu trang (Ví dụ: `12h 30m`).
* **Các trường thông tin hiển thị**:
  - Trạng thái giấc ngủ: Bắt đầu ngủ (Start Sleep) / Thức dậy (Wake up).
  - Tổng thời lượng của cữ ngủ đó (Ví dụ: *Ngủ trưa: 1 tiếng 45 phút*).
  - Ghi chú chất lượng giấc ngủ (Giật mình, ngủ ngon, quấy...).
* **Form Thêm mới**:
  - Nút bấm nhanh **`[ Bắt đầu Ngủ ]`**: Tự động lưu mốc thời gian bắt đầu. Khi bé thức dậy, mẹ bấm nút **`[ Đã thức dậy ]`** để tự động tính toán tổng thời gian và lưu lại.
  - Hoặc nhập thủ công: Chọn giờ bắt đầu $\rightarrow$ Chọn giờ thức dậy.

---

### 💩 Phân hệ 3: Vệ sinh & Thay tã (Diaper Logs)
* **Giao diện chính**: Danh sách lịch sử các lần thay tã kèm thẻ màu hiển thị tính chất chất thải của bé (giúp phát hiện sớm các vấn đề tiêu hóa).
* **Các trường thông tin hiển thị**:
  - Loại vệ sinh: Tã ướt (Wet), Tã bẩn (Dirty), Cả hai (Both).
  - Màu sắc phân: Vàng, Xanh lá, Nâu, Đỏ (Cảnh báo nguy hiểm).
  - Tính chất: Lỏng, Đặc, Nhầy, Có bọt.
  - Thời gian thay tã.
* **Form Thêm mới**:
  - Bộ nút chọn nhanh (Radio button dạng hình vẽ): Chọn loại tã (Ướt/Bẩn).
  - Bảng màu chọn nhanh: Chọn màu sắc phân thực tế.
  - Dropdown chọn tính chất phân.

---

## 💡 3. Các hiệu ứng Micro-interactions tăng trải nghiệm người dùng
1. **Lọc thông minh (Smart Filtering)**: Cho phép cha mẹ lọc nhanh danh sách theo ngày hôm nay, hôm qua hoặc 7 ngày gần nhất.
2. **Animation đồng bộ**: Khi Agent trích xuất dữ liệu thành công từ khung chat (ở AI Room), một hiệu ứng chuyển động nhỏ (Slide-in card) sẽ bay từ góc màn hình vào bảng lịch sử hoạt động để phụ huynh cảm thấy hệ thống phản hồi tức thì.
3. **Cảnh báo bất thường (Health Flag)**: Nếu trong bảng lịch sử thay tã ghi nhận màu phân đỏ/đen, hoặc biểu đồ ngủ ghi nhận bé ngủ ít hơn 8 tiếng/ngày, thẻ hoạt động đó sẽ hiển thị viền đỏ nhấp nháy nhẹ kèm biểu tượng cảnh báo ⚠️ để nhắc mẹ hỏi ý kiến bác sĩ.
