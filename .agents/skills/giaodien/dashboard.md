# Yêu cầu Thiết kế Giao diện Dashboard (Dashboard UI Requirements)

Tài liệu này cung cấp các yêu cầu chức năng, bố cục, các token thiết kế (Design System) và hình ảnh bản mẫu giao diện cao cấp dành cho **Trang chủ Dashboard** của hệ thống BabyCare AI.

---

## 🎨 1. Định hướng Thiết kế & Thẩm mỹ (Aesthetics & Theme)
* **Phong cách**: Modern Glassmorphism (phủ kính mờ hiện đại), các cạnh bo tròn mềm mại tạo cảm giác thân thiện với trẻ nhỏ.
* **Tông màu chủ đạo**: Pastel nhẹ nhàng, ấm áp và y khoa:
  - Màu nền: Soft Cream (`#FAF9F6`) hoặc Light Mint/Blue (`#F0F8FF`).
  - Màu nhấn (Accent): Soft Blue (cho Bé trai), Warm Peach/Pink (cho Bé gái), Mint Green (Trạng thái bình thường/Y tế).
* **Typography**: Sử dụng các phông chữ hiện đại, rõ nét và dễ thương như `Outfit`, `Inter` hoặc `Nunito`.

---

## 📸 2. Bản mẫu Thiết kế Giao diện (UI Mockup)
Dưới đây là thiết kế giao diện trực quan cao cấp cho trang Dashboard để nhóm phát triển Frontend triển khai:

![Bản mẫu giao diện BabyCare AI Dashboard](C:\Users\ASUS\.gemini\antigravity-ide\brain\f22e2574-ea3e-4d3e-b65b-3248594ef5c9\babycare_dashboard_mockup_1784281178677.png)

---

## 🧱 3. Bố cục & Các Phân khu Chức năng (Layout & Widgets)

Bố cục Dashboard được chia thành **3 vùng cột chính**:

### ⬅️ Cột Trái: Thanh điều hướng (Navigation Sidebar)
Thanh thực đơn điều hướng mượt mà, cố định (Sticky):
1. **Tổng quan (Dashboard)**: Trang chủ hiển thị nhanh thông tin.
2. **Trợ lý AI (AI Chat Room)**: Phòng hội thoại chi tiết với Agent.
3. **Nhật ký hoạt động**: Bộ lọc xem Ăn uống, Giấc ngủ, Vệ sinh.
4. **Hồ sơ sức khỏe**: Quản lý bệnh lý, lịch sử dùng thuốc, tiêm chủng.
5. **Biểu đồ tăng trưởng**: Biểu đồ WHO chiều cao, cân nặng.
6. **Báo cáo**: Xuất báo cáo định kỳ.

---

### 🏛️ Cột Giữa (Phần trung tâm): Widget Chính & Tương tác

#### 1. Header Chọn Hồ sơ Bé & Phím tắt nhanh (Quick Actions)
* **Bộ chọn bé**: Dropdown hiển thị tên bé đang chọn (Ví dụ: `"Bé Bo - 6 tháng tuổi"`).
* **Nhóm phím tắt nhanh**:
  - 🍼 Ghi ăn sữa.
  - 💤 Ghi giấc ngủ.
  - 💩 Ghi thay tã.
  - 💊 Ghi dùng thuốc.

#### 2. Thẻ trạng thái hiện tại (Quick Status Cards)
Hiển thị các chỉ số đo gần nhất của bé dưới dạng Card phủ kính:
* **🍼 Bú/Ăn**: Lần cuối bú cách đây 2 tiếng (150ml sữa công thức).
* **💤 Ngủ**: Hôm nay bé đã ngủ 12 tiếng 30 phút.
* **💩 Vệ sinh**: Đã thay tã 3 lần trong ngày (phân bình thường).
* **🌡️ Thân nhiệt**: 36.8°C (Ổn định).

#### 3. Khung Chat AI Tương tác trực tiếp (Interactive AI Chat Widget)
* **Vị trí**: Đặt tại khu vực trung tâm nổi bật.
* **Tính năng**: 
  - Khung chat thu nhỏ giúp mẹ có thể gõ nhanh lệnh hoặc bấm **nút Mic** để thu âm giọng nói trực tiếp (Ví dụ: *"Ghi nhận giúp tôi bé vừa bú 150ml..."*).
  - Có hiệu ứng sóng âm (Microphone waves animation) khi đang thu âm.
  - Phản hồi từ Agent hiện ngay trong khung chat kèm thẻ tag trạng thái được trích xuất (Ví dụ: `next_step: feeding`).

#### 4. Biểu đồ tăng trưởng WHO (Growth Tracking Chart)
* **Loại biểu đồ**: Biểu đồ đường (Line Chart - dùng Chart.js hoặc Recharts).
* **Nội dung**: Hiển thị đường phát triển chiều cao/cân nặng của bé thực tế đè lên các dải phân vị chuẩn của WHO (Percentiles: 3rd, 50th, 97th) để phụ huynh biết bé có đang phát triển tốt hay không.

---

### ➡️ Cột Phải: Dòng thời gian & Khuyến nghị y tế

#### 1. Dòng thời gian hoạt động trong ngày (Activity Timeline)
* Hiển thị danh sách các hoạt động vừa ghi nhận theo thứ tự thời gian giảm dần (mới nhất ở trên):
  - *12:30* - 💤 Bé bắt đầu đi ngủ trưa.
  - *12:00* - 🍼 Bé bú 150ml sữa công thức.
  - *08:00* - 💊 Uống Hapacol 150mg (sốt 38.5°C).

#### 2. Thẻ gợi ý/Khuyến nghị từ Trí tuệ nhân tạo (AI Recommendations)
* Hiển thị các phân tích thông minh từ Agent dựa trên dữ liệu nhật ký:
  - *Khuyến nghị*: *"Bé Bo đã đủ 6 tháng tuổi, mẹ có thể bắt đầu cho bé tập ăn dặm bằng cháo rây loãng tỷ lệ 1:10 kết hợp bí đỏ nghiền..."*
  - *Cảnh báo y tế*: *"Nhắc nhở: Cữ thuốc hạ sốt Hapacol tiếp theo của bé chỉ được uống sau 14:00 nếu sốt lại."*

---

## 💾 4. Ánh xạ Chi tiết Dữ liệu giữa API/Firestore và Frontend
Để đảm bảo giao diện hiển thị chính xác theo đúng cấu trúc cơ sở dữ liệu hiện tại, dưới đây là ánh xạ thực thể chi tiết:

### 👶 1. Thông tin Hồ sơ Bé (Baby Profile)
* **API Schema**: `BabyResponse` (trong [app/modules/baby/schemas.py](file:///d:/ViT/BABYCARE/babycare-ai/app/modules/baby/schemas.py))
* **Dữ liệu hiển thị ở Giao diện**:
  - Tên bé: `name` (String)
  - Ngày sinh: `birth_date` (String - Định dạng `YYYY-MM-DD` để hiển thị và tính tuổi của bé theo tháng)
  - Giới tính: `gender` (String - Giá trị: `boy`, `girl`, `unknown` dùng để đổi màu sắc Theme pastel)
  - Mã định danh: `id` (String - để truyền vào `baby_id` cho các API khác)

### 📈 2. Biểu đồ tăng trưởng WHO (Growth Tracking Chart)
* **API Schema**: `GrowthLogResponse` (trong [app/modules/growth_tracking/schemas.py](file:///d:/ViT/BABYCARE/babycare-ai/app/modules/growth_tracking/schemas.py))
* **Dữ liệu hiển thị ở Giao diện**:
  - Trục hoành (Thời gian): `logged_at` (String - mốc thời gian đo) hoặc `who_status.age_in_months` (Float - Tuổi tính theo tháng để vẽ trục hoành đối chiếu)
  - Cân nặng: `weight` (Float - kg)
  - Chiều cao: `height` (Float - cm)
  - Vòng đầu (nếu có): `head_circumference` (Float - cm)
  - Trạng thái phân tích WHO (để tô màu cảnh báo nhanh): `who_status.weight_status` (`underweight`, `normal`, `overweight`) và `who_status.height_status` (`stunted`, `normal`, `tall`)

### 🍼 3. Nhật ký Ăn dặm (Solid Food Logs)
* **API Schema**: `SolidFoodLogResponse` (trong [app/modules/nutrition/schemas.py](file:///d:/ViT/BABYCARE/babycare-ai/app/modules/nutrition/schemas.py))
* **Dữ liệu hiển thị ở Giao diện**:
  - Tên món ăn/loại sữa: `food_name` (String)
  - Lượng ăn: `amount_g` (Float - biểu diễn lượng gram ăn dặm hoặc ml sữa)
  - Phản ứng của bé (hiển thị biểu tượng cảm xúc icon): `reaction` (String - Giá trị: `like` (thích), `dislike` (ghét), `allergic` (dị ứng), `vomit` (trớ))
  - Thời gian: `logged_at` (String - ISO 8601 hiển thị giờ ăn trên dòng thời gian)
  - Ghi chú: `notes` (String)

### 💩 4. Nhật ký Triệu chứng sức khỏe & Khám bệnh (Health Records)
* **API Schema**: `HealthRecordResponse` (trong [app/modules/health_records/schemas.py](file:///d:/ViT/BABYCARE/babycare-ai/app/modules/health_records/schemas.py))
* **Dữ liệu hiển thị ở Giao diện**:
  - Triệu chứng (hiển thị dạng các nhãn tag): `symptoms` (List[String] - Ví dụ: `["sốt", "nổi mẩn", "quấy khóc"]`)
  - Chẩn đoán: `diagnosis` (String - hiển thị nếu bác sĩ đã chẩn đoán)
  - Đơn thuốc/Điều trị: `treatment` (String)
  - Tên bác sĩ khám: `doctor_name` (String)
  - Thời gian ghi nhận: `recorded_at` (String)

### 💊 5. Nhật ký uống thuốc/Vitamin (Medication Logs)
* **API Schema**: `MedicationLogResponse` (trong [app/modules/medication/schemas.py](file:///d:/ViT/BABYCARE/babycare-ai/app/modules/medication/schemas.py))
* **Dữ liệu hiển thị ở Giao diện**:
  - Tên thuốc/Vitamin: `medication_name` (String)
  - Liều lượng: `dosage` (String - Ví dụ: `1 gói 150mg`, `2 giọt`)
  - Chỉ định bởi: `prescribed_by` (String)
  - Thời gian uống: `logged_at` (String)

### 🔊 6. Nhật ký Tiếng khóc & Vỗ về (Cry Logs)
* **API Schema**: `CryLogResponse` (trong [app/modules/cry/schemas.py](file:///d:/ViT/BABYCARE/babycare-ai/app/modules/cry/schemas.py))
* **Dữ liệu hiển thị ở Giao diện**:
  - File âm thanh (để bấm phát trực tiếp): `audio_url` (String - liên kết Firebase Storage)
  - Dự đoán nguyên nhân khóc: `prediction` (String - Giá trị: `hungry`, `tired`, `pain`, `diaper`, `discomfort`)
  - Độ tin cậy (hiển thị dạng phần trăm): `confidence` (Float - Ví dụ: `0.85` hiển thị `85%`)
  - Đánh giá của cha mẹ: `feedback_accurate` (Boolean - nút Thích/Không thích để đánh giá độ chuẩn xác của AI)
  - Nhạc vỗ về đã phát: `sound_played` (String)
  - Thời điểm bé khóc: `logged_at` (String)
