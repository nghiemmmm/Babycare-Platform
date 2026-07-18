mô tả kỹ thuật chi tiết cho trang Baby Profile & Caregiver Sync (Hồ sơ của Bé & Kết nối người chăm sóc). Trang này là trung tâm quản trị danh tính số của bé và quản lý vòng tròn gia đình, sử dụng ngôn ngữ thiết kế Serene Parent ([Design_System]).

1. Phong cách thiết kế & Thông số Kỹ thuật (Technical Specs)
- Font chữ: Quicksand (Sans-serif, các nét tròn trịa, tạo cảm giác thân thiện và hiện đại).
- Aesthetic: Soft Minimalism kết hợp với các khối nội dung lớn, rõ ràng.
- Hệ màu (Color Palette):
  - Primary Navy: #1c648e (Tiêu đề, text chính, nút lưu).
  - Background: Xám trắng nhạt (#f8f9ff).
  - Accent Green: #4d7c0f (Dùng cho khu vực mời người thân, tạo cảm giác tích cực).
  - Neutral Blue: Các tone màu xanh nhạt của hệ thống (Surface-container).
- Hiệu ứng (Visual Effects):
  - Sử dụng đổ bóng nhẹ (shadow-sm) để tách biệt các thẻ (cards).
  - Bo góc (Border Radius) cực lớn (rounded-[32px]) cho các panel chính và rounded-full cho avatar/nút.

2. Bố cục & Hệ thống Nút (Layout & Interactive Elements)
Giao diện được chia thành 3 khu vực chức năng chính:

A. Header & Profile Selector (Top Section)
- Profile Tabs: Hệ thống tab nằm ngang phía trên cùng để chuyển đổi giữa các bé (ví dụ: Bé Bo).
- Nút "+ Add New Baby": Nút dạng thẻ mỏng với icon cộng để thêm hồ sơ mới vào hệ thống.

B. Cột Trái (60%): Thông tin chi tiết của Bé (Bo's Profile)
- Avatar Editor: Hình ảnh bé Bo trong khung tròn lớn (128px) với nút "Camera Icon" (rounded-full, màu Navy) đè lên để thay đổi ảnh.
- Form Inputs: Các trường nhập liệu (Name, Birth Date) với viền mỏng, bo góc lớn, text hiển thị rõ ràng.
- Gender Selector: Nhóm nút radio tùy chỉnh lớn. Nút "Girl" đang ở trạng thái Active với nền xanh nhạt và viền xanh Navy đậm.
- Nút "Save Changes": Nút hành động chính (Primary Action), màu Navy đậm, bo góc tròn (Pill-shaped).
- Nút "+ Add New Baby" (Phụ): Nút thứ cấp màu xanh nhạt nằm cạnh nút lưu.

C. Cột Phải (40%): Quản lý người giám hộ (Guardian Sync)
- Invite Guardian Card: Một thẻ đặc biệt có viền xanh lá đậm.
- Input "Email Address": Ô nhập liệu tối giản.
- Nút "Send Invitation": Nút màu xanh lá đậm với icon mũi tên/gửi.
- Active Guardians List: Danh sách dọc hiển thị những người đã kết nối.
  - Admin Badge: Label màu xanh lá nhạt cho tài khoản Admin.
  - Nút "Delete/Trash": Icon thùng rác màu đỏ để xóa người chăm sóc (ví dụ: Nanny Maria).
  - Nút "Resend": Nút text màu xanh cho các lời mời đang chờ (Pending).
- Family Status Widget: Panel dưới cùng hiển thị trạng thái đồng bộ ("All Synced Up!") với màu gradient xanh dương mềm mại.

3. Thông số kỹ thuật cho Prompt Code (Tailwind CSS)
- Grid Layout: Sử dụng grid grid-cols-12 gap-6 cho Desktop (Cột trái chiếm 7-8 cột, cột phải chiếm 4-5 cột).
- Card Style: bg-white rounded-[32px] p-8 shadow-sm border border-slate-100.
- Input Style: w-full px-4 py-3 rounded-2xl border border-slate-200 focus:border-primary.
