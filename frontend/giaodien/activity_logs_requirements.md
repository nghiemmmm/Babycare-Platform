Trang này được thiết kế theo phong cách Serene Parent ([Design_System_2]), tối ưu hóa cho việc quản lý và xem lại dữ liệu lịch sử của bé một cách trực quan.

1. Phong cách thiết kế (Visual Aesthetic)
Chủ đạo: Modern Minimalist kết hợp với Soft Glassmorphism.
Bố cục: Chia làm 2 khu vực chính: Sidebar điều hướng cố định (trái) và Vùng nội dung dữ liệu (phải).
Hiệu ứng: Sử dụng backdrop-blur nhẹ cho sidebar, các thẻ nội dung (cards) có độ bo góc lớn (24px - 32px) và đổ bóng cực mịn (shadow-sm).

2. Hệ thống Typography & Màu sắc
Font chữ: Quicksand (Font chữ tròn trịa, thân thiện với cha mẹ).
Màu sắc:
Primary: Deep Navy (#1c648e) cho các tiêu đề và trạng thái nhấn mạnh.
Active Tab: Sử dụng màu xanh Navy đậm với thanh underline phía dưới.
Background: Trắng mờ hoặc xám nhạt cực loãng để làm nổi bật các khối nội dung trắng.

3. Cấu trúc Layout chi tiết
Top Bar (Header):
- Tiêu đề trang "Daily Log" (font-bold).
- Hệ thống chuyển đổi Tab nhanh: Feeding, Sleep, Diapering (Nằm cạnh tiêu đề chính).

Vùng Tab Content (Main Panel):
- Tab Navigation: Một thanh tab lớn bên trong panel chính (Feeding, Sleep, Diaper) với hiệu ứng active rõ rệt.
- Summary Card: Khối nội dung phía trên hiển thị tổng quan (Ví dụ: "Total Volume: 850ml" cho Feeding).
- Timeline View: Dòng thời gian lịch sử chi tiết ở phía dưới, hiển thị các bản ghi theo thứ tự thời gian.

Sidebar (Left Navigation):
- Hiển thị hồ sơ bé hiện tại (Avatar, tên, tuổi).
- Danh sách menu: Dashboard, Daily Log (Active), Baby Profile, AI Hub, Nutrition, Growth, Health, Photos.
- Nút hành động chính: + Log New Activity (Primary Action Button).

4. Thông số kỹ thuật cho Prompt
CSS Framework: Tailwind CSS.
Sidebar Width: ~260px.
Glassmorphism Card: bg-white/60 backdrop-blur-md border border-white/20.
Interactive Elements: Nút "Log New Activity" sử dụng màu Primary Navy, bo góc tròn hoàn toàn (pill-shaped).
