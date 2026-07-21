mô tả kỹ thuật chi tiết của trang Health & Medication (Sổ Sức khỏe & Thuốc). Đây là trang quan trọng nhất về tính an toàn trong hệ thống BabyCare AI, sử dụng ngôn ngữ thiết kế Serene Parent ([Design_System]).

1. Phong cách thiết kế & Thông số Kỹ thuật (Technical Specs)
- Font chữ: Quicksand (Sans-serif, tròn trịa, dễ đọc và thân thiện).
- Hiệu ứng (Visual Effects):
  - Glassmorphism: Các thẻ (Cards) sử dụng bg-white/60 kết hợp backdrop-blur-xl.
  - Borders: Viền siêu mỏng border-white/20 để tách biệt các lớp kính.
  - Bo góc (Radius): Cực lớn (rounded-[32px]) tạo cảm giác mềm mại, an toàn.
- Hệ màu (Color Palette):
  - Primary Navy: #1c648e (Tiêu đề, icon chính).
  - Alert Red: #ef4444 (Dành riêng cho cảnh báo an toàn liều lượng).
  - Safety Orange: #f97316 (Dành cho các mục cần lưu ý hoặc đo nhiệt độ).
  - Healthy Green: #22c55e (Trạng thái ổn định/đã xác nhận).

2. Bố cục & Hệ thống Nút (Layout & Interactive Elements)
Trang được chia thành cấu trúc Sidebar cố định và Nội dung 2 cột (65/35):

A. Header & Cảnh báo (Top Section)
- Safety Alert Banner: Nằm trên cùng, màu đỏ nhạt (bg-red-50), có viền trái dày 4px màu đỏ đậm. Hiển thị cảnh báo liều lượng vượt mức.
- Page Header: Tiêu đề "Health Dashboard" kèm nút "Family Sync" (thể hiện trạng thái đồng bộ thời gian thực).

B. Cột Trái (65%): Nhật ký Y tế (Medical Incidents)
- Nút "Add Medical Record": Nút hành động chính dạng Pill-shaped, màu xanh nhạt (bg-sky-100) với icon dấu cộng.
- Thẻ Sự cố (Incident Cards):
  - Symptom Tags: Các nút pill nhỏ màu pastel (Cam cho Fever, Đỏ nhạt cho Cough) để lọc nhanh triệu chứng.
  - Status Badge: Góc trên phải (Confirmed/Healthy) để phân loại mức độ nghiêm trọng.
  - Treatment Block: Vùng nội dung màu xanh nhạt (bg-blue-50/50) hiển thị phác đồ điều trị chi tiết.

C. Cột Phải (35%): Quản lý Thuốc (Medication Management)
- Countdown Widget: Thẻ quan trọng nhất hiển thị bộ đếm ngược thời gian thực (HH:MM:SS) cho liều tiếp theo.
- Nút "DO NOT ADMINISTER": Trạng thái nút bị vô hiệu hóa (Disabled) màu đỏ khi chưa đến giờ uống thuốc để tránh nhầm lẫn.
- Recent Doses List: Danh sách dọc các liều đã dùng với icon đặc trưng cho từng loại thuốc (viên nén, siro).
- Nút "View Medication History": Nút Outline (viền nét đứt) ở cuối cột phải để xem lịch sử chuyên sâu.

D. Chân trang (Sidebar Integration)
- Nút "Quick Log": Nút nổi bật nhất màu Navy đậm ở cuối Sidebar trái để thêm nhanh nhật ký từ bất kỳ đâu.

3. Thông số kỹ thuật cho Prompt Code
- "Sử dụng CSS Grid để chia cột 65/35 cho Desktop."
- "Tạo component Countdown động dựa trên biến next_dose_time."
- "Banner cảnh báo phải có hiệu ứng rung nhẹ (pulse) để thu hút sự chú ý nếu có dữ liệu nguy hiểm từ API."
