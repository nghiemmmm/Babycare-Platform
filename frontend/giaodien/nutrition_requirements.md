mô tả kỹ thuật chi tiết cho trang Nutrition & Solid Food AI (Dinh dưỡng & Ăn dặm AI). Trang này được thiết kế để giúp cha mẹ quản lý hành trình ăn dặm của bé một cách khoa học và an toàn, sử dụng ngôn ngữ thiết kế Serene Parent ([Design_System]).

1. Phong cách thiết kế & Thông số Kỹ thuật (Technical Specs)
- Aesthetic (Thẩm mỹ): Soft Medical Serenity. Giao diện kết hợp giữa sự chuyên nghiệp của y tế và sự ấm áp của gia đình, sử dụng cấu trúc các lớp kính (Glassmorphism) mờ nhẹ trên nền sáng.
- Font chữ: Quicksand (Sans-serif với các nét trơn, mang lại cảm giác an tâm, hiện đại và rất dễ đọc).
- Hệ màu (Color Palette):
  - Primary Navy: #1c648e (Dùng cho tiêu đề, icon chính và các nút quan trọng).
  - Success Green: #22c55e (Nhãn "Loved it" và các chỉ số tích cực).
  - Warning Orange: #f97316 (Nhãn "Spat out" hoặc các thực phẩm cần lưu ý).
  - Danger Red: #ef4444 (Dành riêng cho cảnh báo dị ứng "High Alert").
  - Soft Mint: #ecfdf5 (Màu nền cho các gợi ý AI Meal Plan).
- Hiệu ứng (Visual Effects):
  - Bo góc cực lớn (rounded-[32px]) cho tất cả các Panel và Card chính.
  - Đổ bóng mềm (Shadow-sm) và viền mờ (border-white/20) để tạo chiều sâu và sự tách biệt rõ ràng giữa các vùng nội dung.

2. Bố cục & Hệ thống Nút (Layout & Interactive Elements)
Trang sử dụng bố cục Sidebar cố định bên trái và nội dung chính chia làm 2 cột không đối xứng (tỷ lệ khoảng 60/40):

A. Header & Hệ thống điều hướng (Top Section)
- Page Title: "Nutrition & Solids" kèm Badge "Family Sync" màu xanh lá (thể hiện trạng thái đồng bộ dữ liệu thời gian thực giữa các thành viên gia đình).
- Nút hành động:
  - Nút "Export Log": Nút Outline (viền mỏng), dùng để xuất báo cáo dinh dưỡng gửi cho bác sĩ.
  - Nút "+ New Entry": Nút hành động chính (Primary CTA), màu Navy đậm, bo góc tròn (Pill-shaped), có icon dấu cộng nổi bật.

B. Cột Trái (60%): Nhật ký & Tiến trình ăn dặm
- Feeding Log Summary: Thẻ kính lớn hiển thị 3 chỉ số quan trọng: Milk Intake (Lượng sữa), Solids (Số bữa ăn dặm), và Next Feed (Lịch bú tiếp theo). Sử dụng các thanh tiến trình (Progress Bar) để trực quan hóa mục tiêu dinh dưỡng trong ngày.
- Timeline: Một dòng thời gian ngắn hiển thị các hoạt động gần nhất (ví dụ: 180ml Formula lúc 08:00 AM).
- New Ingredients Track: Danh sách các thực phẩm mới được giới thiệu cho bé.
- Reaction Badges: Các nhãn phản hồi cảm xúc: "Loved it" (Xanh lá - Thích), "Spat out" (Cam - Nhè ra).
- Search/Filter: Icon kính lúp và bộ lọc ở góc phải để tìm kiếm lịch sử nguyên liệu.
- Quick Action Row (Chân trang): 4 thẻ hành động nhanh: "Scan Meal" (Quét bữa ăn bằng AI), "Recipe Book" (Công thức nấu ăn), "Ask Expert" (Chat với chuyên gia), và "Grocery List" (Danh sách mua sắm).

C. Cột Phải (40%): AI Insights & An toàn thực phẩm
- AI Meal Plan Widget: Một Panel nổi bật với nền xanh Mint nhạt.
- Food Recommendation Cards: Các thẻ thực phẩm gợi ý (Bơ, Cải bó xôi) với hình ảnh tròn và mô tả lợi ích (ví dụ: Giàu chất béo tốt).
- Nút "View Weekly Plan": Nút hành động ở cuối thẻ với icon mũi tên để xem kế hoạch ăn uống cả tuần.
- Allergen Safety Panel: Khu vực an toàn quan trọng nhất.
  - High Alert Box: Màu đỏ nhạt (bg-red-50) cảnh báo về các thực phẩm nguy cơ dị ứng cao (ví dụ: Đậu phộng).
  - Foods to Avoid (Until 1yr): Danh sách các thực phẩm cấm trước 1 tuổi (Mật ong, Muối, Đường) với icon thông tin (i) để xem giải thích y khoa.
  - Nút "View Full Safety Guide": Nút rộng 100%, màu xanh dương nhạt, dùng để mở cẩm nang an toàn thực phẩm đầy đủ.

3. Thông số kỹ thuật cho Prompt Code (Tailwind CSS)
- Layout: grid grid-cols-12 gap-6.
- Card Style: bg-white/60 backdrop-blur-xl border border-white/20 rounded-[32px] p-6.
- Floating Action Button (FAB): Nút Navy đậm (bg-[#1c648e]) với icon dấu cộng nằm ở góc dưới cùng bên phải để thêm nhật ký nhanh chóng từ bất kỳ đâu.
