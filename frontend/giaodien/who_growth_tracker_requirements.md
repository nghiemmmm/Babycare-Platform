mô tả kỹ thuật chi tiết cho trang WHO Growth Tracker (Theo dõi Tăng trưởng WHO). Trang này được thiết kế để cung cấp cái nhìn chuyên sâu về sự phát triển thể chất của bé dựa trên tiêu chuẩn y khoa, sử dụng ngôn ngữ thiết kế Lullaby Glass (Design System [Design_System]).

1. Phong cách thiết kế & Thông số Kỹ thuật (Technical Specs)
- Aesthetic: Advanced Glassmorphism. Giao diện sử dụng nhiều lớp kính (glass panels) chồng lên nhau với độ mờ đục khác nhau để tạo chiều sâu.
- Font chữ: Outfit (Sans-serif, hiện đại, sắc nét và chuyên nghiệp).
- Hiệu ứng (Visual Effects):
  - Main Panels: bg-white/60 kết hợp backdrop-blur-xl và đổ bóng mềm.
  - Bo góc (Radius): Đồng bộ rounded-[32px] cho các thẻ lớn và rounded-2xl cho các thẻ con bên trong.
- Hệ màu (Color Palette):
  - Primary Navy: #1c648e (Dùng cho các đường biểu đồ chính, tiêu đề bảng).
  - Status Colors:
    - Normal (Green): #22c55e (Nền xanh nhạt, chữ xanh đậm).
    - Alert (Red/Orange): #ef4444 (Dùng cho "Risk of Stunting" hoặc các chỉ số ngoài vùng an toàn).
  - Chart Accents: Các đường dashed (đứt nét) màu xám nhạt cho bách phân vị (percentiles).

2. Bố cục & Hệ thống Nút (Layout & Interactive Elements)
Giao diện được chia thành 3 tầng nội dung theo chiều dọc:

A. Tầng 1: Summary Hero Cards (Chỉ số hiện tại)
- Cấu trúc: 3 thẻ kính nằm ngang hiển thị Weight, Height, và Head Circumference.
- Thông số nút/thẻ:
  - Status Badge: Nằm ở góc trên phải mỗi thẻ, sử dụng pill-shape với màu nền pastel tương ứng với trạng thái (Normal/Risk).
  - Trend Indicator: Các icon mũi tên kèm chỉ số thay đổi (ví dụ: +0.4kg since last month) nằm dưới giá trị chính.
  - Icon Context: Mỗi thẻ có một icon đặc trưng (Cân, thước dây, đầu bé) nằm trong khối màu pastel bo góc.

B. Tầng 2: Growth Curve Analysis (Biểu đồ tăng trưởng)
- Bố cục: Một bảng kính lớn chiếm trọn chiều rộng trang.
- Nút chuyển đổi (Toggle Switch):
  - Bộ lọc "Weight / Height" ở góc trên phải. Đây là nút dạng Pill-shaped kép: bên Active có màu Primary Navy (#1c648e), bên Inactive có màu xám nhạt.
- Biểu đồ (Chart Area):
  - Sử dụng đường kẻ đậm có các node (điểm dữ liệu) cho chỉ số của bé.
  - Vùng bách phân vị (3rd - 97th) được thể hiện bằng các đường đứt nét tinh tế để không làm rối mắt.

C. Tầng 3: Measurement History (Bảng lịch sử số đo)
- Header Section:
  - Nút "Add New Measurement": Nút hành động chính (Primary Call-to-Action) màu Navy đậm, bo góc tròn, có icon dấu cộng trắng bên trong.
- Data Table:
  - Các hàng có khoảng cách (padding) rộng rãi, font chữ text-slate-600.
  - Status Dots: Cột cuối cùng sử dụng các chấm màu (Xanh/Đỏ) kèm text trạng thái để đánh giá nhanh theo chuẩn WHO.
  - Action Menu: Icon 3 dấu chấm dọc (More actions) ở cuối mỗi hàng để chỉnh sửa hoặc xóa bản ghi.

3. Thông số kỹ thuật cho Prompt Code (Tailwind CSS)
- Container: max-w-7xl mx-auto p-gutter.
- Glass Card Style: bg-white/40 backdrop-blur-md border border-white/20 shadow-xl.
- Typography Hierarchy:
  - Page Title: text-3xl font-bold text-primary tracking-tight.
  - Card Values: text-4xl font-semibold text-slate-800.
  - Table Headers: bg-blue-50/50 text-primary uppercase text-xs font-bold.
