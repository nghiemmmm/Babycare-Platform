# Yêu cầu Thiết kế Trang Sổ Sức khỏe & Thuốc (Health & Medication Page)

Trang **Sổ Sức khỏe & Thuốc** là trung tâm theo dõi y tế, bệnh án của bé, đồng thời đóng vai trò là "chốt chặn an toàn" cảnh báo liều dùng thuốc và khoảng cách liều hạ sốt Paracetamol/Ibuprofen cho phụ huynh.

---

## 📸 1. Bản mẫu Thiết kế Giao diện (UI Mockup)
Dưới đây là bản vẽ giao diện quản lý sổ sức khỏe bệnh án và uống thuốc của bé:

![Bản mẫu giao diện Sổ Sức khỏe & Thuốc](C:\Users\ASUS\.gemini\antigravity-ide\brain\f22e2574-ea3e-4d3e-b65b-3248594ef5c9\health_and_medication_page_mockup_1784282207697.png)

---

## 🧱 2. Bố cục & Các Phân hệ Chức năng (Page Layout)

Giao diện được chia thành **2 cột song song (Two-column layout)** để dễ dàng quan sát:

### ⬅️ Cột Trái: Nhật ký Bệnh án & Triệu chứng (Health Records - Khớp `HealthRecordResponse`)
* **Chức năng**: Hiển thị lịch sử các đợt bé bị ốm, sốt, ho, sởi và thông tin khám bệnh.
* **Các trường thông tin hiển thị**:
  - **Triệu chứng (`symptoms`)**: Hiển thị dạng các nhãn tag màu cam/đỏ nổi bật (Ví dụ: `[Sốt 38.8 độ]`, `[Ho khan]`, `[Nổi mẩn đỏ]`).
  - **Chẩn đoán (`diagnosis`)**: Ví dụ: *Viêm họng cấp*, *Sốt mọc răng*.
  - **Phương pháp điều trị/Đơn thuốc (`treatment`)**: Danh sách các thuốc bác sĩ kê và cách sử dụng.
  - **Tên bác sĩ (`doctor_name`)** và Ghi chú (`notes`).
  - **Thời gian ghi nhận (`recorded_at`)**.
* **Form Thêm mới (Thủ công)**: Modal `+ Thêm bệnh án`:
  - Input tags: Nhập triệu chứng.
  - Input text: Chẩn đoán, phương án điều trị, tên bác sĩ.
  - Textarea: Ghi chú thêm.
* **Đường dẫn API**: 
  - Lấy lịch sử: `GET /api/health-records/history?baby_id={baby_id}`
  - Ghi mới: `POST /api/health-records/record?baby_id={baby_id}`

---

### ➡️ Cột Phải: Nhật ký Uống thuốc & Vitamin (Medications - Khớp `MedicationLogResponse`)
* **Chức năng**: Theo dõi cữ dùng thuốc thực tế của bé, phục vụ việc đối chiếu liều dùng an toàn.
* **Các trường thông tin hiển thị**:
  - Tên thuốc/Vitamin: `medication_name` (Ví dụ: *Hapacol 150mg*, *Vitamin D3 K2*).
  - Liều lượng: `dosage` (Ví dụ: *1 gói*, *2 giọt*).
  - Chỉ định bởi: `prescribed_by` (Bác sĩ nhi khoa kê hay bố mẹ tự bổ sung).
  - Thời gian cho bé uống thuốc: `logged_at` (Hiển thị giờ chi tiết).
* **Form Thêm mới**: Modal `+ Ghi nhận cữ uống thuốc`:
  - Input text: Tên thuốc, liều lượng dùng.
  - Dropdown: Chọn người kê đơn (Bác sĩ / Tự bổ sung).
  - Date/Time picker: Thời điểm uống thuốc thực tế.

---

## 🚨 3. Các Tính năng Cảnh báo An toàn & Thông minh (Safety & Smart Features)

### 1. Đồng hồ đếm ngược khoảng cách liều (Medication Dose Interval Counter)
* **Quy tắc**: Thuốc hạ sốt Paracetamol chỉ được phép uống cách nhau tối thiểu 4-6 tiếng.
* **Giao diện**: Khi trong danh sách có ghi nhận một cữ thuốc hạ sốt Paracetamol (Ví dụ: *Hapacol* hoặc *Sotstop*):
  - Hệ thống tự động tính toán thời điểm được phép uống cữ tiếp theo (Giờ đã uống + 4 tiếng).
  - Hiển thị widget **Đồng hồ đếm ngược (Countdown Timer)** màu vàng cảnh báo ở đầu cột phải: *"Thời gian chờ cữ tiếp theo: 02 giờ 15 phút"* kèm trạng thái ❌ **CHƯA ĐƯỢC UỐNG**.
  - Khi đồng hồ đếm ngược về 0, widget đổi sang màu xanh mint với biểu tượng 🟢 **ĐỦ ĐIỀU KIỆN UỐNG**.

### 2. Cảnh báo quá liều y khoa
* Nếu phụ huynh nhập thủ công liều Paracetamol lớn hơn 15mg/kg trọng lượng cơ thể bé (lấy thông số cân nặng từ biểu đồ tăng trưởng gần nhất), giao diện sẽ hiển thị cảnh báo đỏ nổi bật: ⚠️ **Cảnh báo: Liều lượng này vượt quá khuyến nghị an toàn cho cân nặng của bé (tối đa {max_dose}mg). Hãy kiểm tra kỹ hướng dẫn sử dụng!**

---

## 💾 4. Luồng dữ liệu & API Tích hợp (API & Data Flow)
1. **Lấy danh sách thuốc**: `GET /api/medication/history?baby_id={baby_id}`
2. **Ghi nhận cữ thuốc**: `POST /api/medication/log?baby_id={baby_id}`
3. **Tính toán đếm ngược**: Frontend lấy thời gian `logged_at` của bản ghi Paracetamol gần nhất từ lịch sử API để tự động chạy hàm đếm ngược (Countdown) trên Client Side.
