# Yêu cầu Thiết kế Trang Theo dõi Tăng trưởng WHO (WHO Growth Tracker Page)

Trang **Theo dõi Tăng trưởng WHO** giúp cha mẹ theo dõi và đánh giá trực quan chỉ số thể chất của bé (Chiều cao, Cân nặng, Vòng đầu) so với chuẩn tăng trưởng quốc tế của Tổ chức Y tế Thế giới (WHO).

---

## 📸 1. Bản mẫu Thiết kế Giao diện (UI Mockup)
Dưới đây là bản vẽ thiết kế giao diện biểu đồ tăng trưởng và bảng quản lý chỉ số của bé:

![Bản mẫu giao diện Theo dõi Tăng trưởng WHO](C:\Users\ASUS\.gemini\antigravity-ide\brain\f22e2574-ea3e-4d3e-b65b-3248594ef5c9\who_growth_tracker_page_mockup_1784282384765.png)

---

## 🧱 2. Bố cục & Các Tính năng Giao diện (Page Layout)

Giao diện được phân chia khoa học thành **3 phân khu chức năng**:

### 1. Thống kê chỉ số hiện tại & Đánh giá nhanh (Current Status & Evaluation)
* Hiển thị 3 chỉ số đo mới nhất của bé dưới dạng số lớn:
  - ⚖️ **Cân nặng**: `7.2 kg` (Đánh giá: 🟢 Bình thường)
  - 📏 **Chiều cao**: `66 cm` (Đánh giá: 🟡 Nguy cơ suy dinh dưỡng thấp còi)
  - 🧠 **Vòng đầu**: `42.5 cm` (Đánh giá: 🟢 Bình thường)
* Dữ liệu đánh giá lấy trực tiếp từ đối tượng `who_status` (`weight_status`, `height_status`) trong cơ sở dữ liệu.

### 2. Biểu đồ Đường cong Tăng trưởng Tương tác (Interactive Growth Curves Chart)
* **Loại biểu đồ**: Biểu đồ đường (Line Chart - khuyến nghị dùng thư viện Recharts hoặc Chart.js).
* **Trục hoành (X-axis)**: Tuổi của bé theo tháng (Ví dụ: từ 0 đến 24 tháng).
* **Trục tung (Y-axis)**: Trọng lượng (kg) hoặc Chiều cao (cm).
* **Đường dữ liệu hiển thị**:
  - **Đường nét đứt màu xám nhạt (WHO Percentiles)**: Biểu diễn các dải chuẩn WHO (`3rd` - Suy dinh dưỡng nặng, `15th` - Nguy cơ suy dinh dưỡng, `50th` - Trung bình chuẩn, `85th` - Thừa cân nhẹ, `97th` - Béo phì/Cao vượt trội).
  - **Đường nét liền màu đậm (Đường thực tế của bé)**: Vẽ nối các điểm đo thực tế của bé để phụ huynh thấy được xu hướng phát triển (đang đi lên, nằm ngang hay đi xuống).
* **Nút bấm lọc**: Cho phép mẹ chọn hiển thị Biểu đồ Cân nặng hoặc Biểu đồ Chiều cao.

### 3. Bảng Lịch sử & Nút Nhập dữ liệu mới (History Table & Form)
* **Bảng lịch sử (Khớp `GrowthLogResponse`)**:
  - Cột 1: Ngày đo (`logged_at`)
  - Cột 2: Cân nặng (`weight` - kg)
  - Cột 3: Chiều cao (`height` - cm)
  - Cột 4: Vòng đầu (`head_circumference` - cm)
  - Cột 5: Đánh giá thể trạng (`who_status`)
  - Cột 6: Hành động (Nút Xóa bản ghi).
* **Nút bấm `+ Thêm số đo mới`**: Mở ra Modal form:
  - Input number: Cân nặng (kg).
  - Input number: Chiều cao (cm).
  - Input number: Vòng đầu (cm - tùy chọn).
  - Date picker: Ngày đo.

---

## 💾 3. Luồng dữ liệu & API Tích hợp (API & Data Flow)

1. **Lấy danh sách lịch sử đo**: `GET /api/growth/history?baby_id={baby_id}`
   - Trả về danh sách đối tượng `GrowthLogResponse` chứa thông số thực tế và đánh giá WHO `who_status`.
2. **Ghi nhận số đo mới**: `POST /api/growth/log?baby_id={baby_id}`
   - Gửi lên payload chứa `height`, `weight`, `head_circumference`. Backend sẽ tự động chạy thuật toán đối chiếu Z-score dựa trên tuổi hiện tại của bé và lưu kết quả WHO tương ứng.
3. **Xóa số đo**: `DELETE /api/growth/log/{log_id}?baby_id={baby_id}`
