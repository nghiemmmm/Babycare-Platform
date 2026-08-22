# Báo cáo Đánh giá Bộ truy xuất Cục bộ (Local Retriever Evaluation Report)

Báo cáo này đánh giá chất lượng của **MedicalRetriever (FAISS + BAAI/bge-m3)** cục bộ bằng các chỉ số định lượng toán học (không dùng LLM-as-a-Judge) để tiết kiệm chi phí API.

---

## 📊 Chỉ số Trung bình Hệ thống (Average Metrics)
* **Mean Hit@1**: `0.83` (Tỷ lệ tìm thấy từ khóa chuẩn trong kết quả đầu tiên)
* **Mean Hit@3**: `1.00` (Tỷ lệ tìm thấy từ khóa chuẩn trong Top 3)
* **Mean Hit@5**: `1.00` (Tỷ lệ tìm thấy từ khóa chuẩn trong Top 5)
* **MRR (Mean Reciprocal Rank)**: `0.92` (Xếp hạng nghịch đảo trung bình của kết quả khớp từ khóa đầu tiên)
* **Mean Recall@3**: `0.58` (Độ phủ của từ khóa trong Top 3 tài liệu)
* **Mean Recall@5**: `0.58` (Độ phủ của từ khóa trong Top 5 tài liệu)

---

## 📝 Chi tiết Đánh giá Từng Kịch bản

| ID | Câu hỏi của Phụ huynh | Từ khóa mong đợi | Hit@1 | Hit@3 | Hit@5 | MRR | Recall@3 | Recall@5 |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| 1 | Chào trợ lý, tôi cần một vài lời khuyên về cách rèn bé sơ sinh tự ngủ. | `['quấy khóc', 'tự ngủ', 'buồn ngủ']` | `1.00` | `1.00` | `1.00` | `1.00` | `0.67` | `0.67` |
| 2 | Bé mấy tháng tuổi thì có thể bắt đầu tập ngồi được vậy bạn? | `['phát triển', 'tháng', 'tập ngồi']` | `1.00` | `1.00` | `1.00` | `1.00` | `0.33` | `0.33` |
| 3 | Bé Bo nhà tôi bị sốt nóng đầu, kẹp nhiệt độ thấy 38.8 độ C thì phải làm sao? | `['sốt', 'Hapacol', 'nhiệt độ', 'Paracetamol']` | `1.00` | `1.00` | `1.00` | `1.00` | `0.75` | `0.75` |
| 4 | Bé uống thuốc hạ sốt Hapacol 150mg lúc 8h sáng, giờ 11h bé lại nóng thì có uống tiếp được không? | `['Hapacol', 'Paracetamol', 'liều', 'tiếng']` | `1.00` | `1.00` | `1.00` | `1.00` | `1.00` | `1.00` |
| 5 | Bé 6 tháng nặng 7.2kg, dài 66cm thì có đạt chuẩn WHO không trợ lý? | `['WHO', 'cân nặng', 'tăng trưởng', 'chuẩn']` | `0.00` | `1.00` | `1.00` | `0.50` | `0.25` | `0.25` |
| 6 | Lên thực đơn ăn dặm tuần đầu tiên cho bé bắt đầu tập ăn dặm từ ngày mai. | `['ăn dặm', 'cháo rây', 'thực đơn', 'nhóm']` | `1.00` | `1.00` | `1.00` | `1.00` | `0.50` | `0.50` |

## 🔍 Nhật ký Nội dung Truy xuất chi tiết (Top 3 Chunks)

### Kịch bản 1: Chào trợ lý, tôi cần một vài lời khuyên về cách rèn bé sơ sinh tự ngủ.
* **Từ khóa mong đợi**: `['quấy khóc', 'tự ngủ', 'buồn ngủ']`
* **Nội dung các phân mảnh truy xuất được (Top 3)**:
  1. "# Hướng dẫn chăm sóc trẻ sơ sinh 1. Trẻ quấy khóc có thể do đói, đầy hơi, tã bẩn, buồn ngủ hoặc quá tải cảm giác. 2. Liều dùng thuốc hạ sốt Hapacol (Paracetamol) cho trẻ em thông thường là 10-15 mg/kg..."
  2. "  Kèm theo thuốc điều trị đúng phác đồ (kháng sinh, hạ sốt ) theo chỉ định  của bác sĩ  Bổ sung vi chất theo khuyến cáo   Vitamin A (theo chương trình bổ sung quốc gia)   Kẽm giúp gi m thời gian ho..."
  3. "## Nguyên tắc khi bé đã được ghi nhận dị ứng với một loại thực phẩm cụ thể  - Tránh hoàn toàn thực phẩm đó và các sản phẩm chứa thành phần từ nó (đọc kỹ nhãn thành phần). - Không tự ý thử lại thực phẩ..."

---

### Kịch bản 2: Bé mấy tháng tuổi thì có thể bắt đầu tập ngồi được vậy bạn?
* **Từ khóa mong đợi**: `['phát triển', 'tháng', 'tập ngồi']`
* **Nội dung các phân mảnh truy xuất được (Top 3)**:
  1. "Dấu hiệu nặng cần đưa trẻ đi bệnh viện ngay.   Thở nhanh theo tuổi (dưới 2 tháng ≥ 60 lần/phút; 2–12 tháng ≥ 50; 1 –5 tuổi  ≥ 40)   Tím tái   Không uống được, bú rất kém hoặc bỏ bú   Co giật   Lơ..."
  2. "## Độ tuổi giới thiệu thực phẩm dễ gây dị ứng  - Không có bằng chứng cho thấy trì hoãn giới thiệu các thực phẩm dễ gây dị ứng sau 6 tháng giúp phòng ngừa dị ứng — ngược lại, giới thiệu sớm (trong giai..."
  3. "# Hướng dẫn chăm sóc trẻ sơ sinh 1. Trẻ quấy khóc có thể do đói, đầy hơi, tã bẩn, buồn ngủ hoặc quá tải cảm giác. 2. Liều dùng thuốc hạ sốt Hapacol (Paracetamol) cho trẻ em thông thường là 10-15 mg/kg..."

---

### Kịch bản 3: Bé Bo nhà tôi bị sốt nóng đầu, kẹp nhiệt độ thấy 38.8 độ C thì phải làm sao?
* **Từ khóa mong đợi**: `['sốt', 'Hapacol', 'nhiệt độ', 'Paracetamol']`
* **Nội dung các phân mảnh truy xuất được (Top 3)**:
  1. "## Khi bé sốt  - Tăng cữ bú/uống nước để bù lượng nước mất qua sốt. - Thức ăn mềm, dễ nuốt, không cần ép ăn nhiều nếu bé mệt và biếng ăn — bù lại bằng cữ bú/sữa. - Chia nhỏ bữa ăn, ưu tiên món bé thíc..."
  2. "# Hướng dẫn chăm sóc trẻ sơ sinh 1. Trẻ quấy khóc có thể do đói, đầy hơi, tã bẩn, buồn ngủ hoặc quá tải cảm giác. 2. Liều dùng thuốc hạ sốt Hapacol (Paracetamol) cho trẻ em thông thường là 10-15 mg/kg..."
  3. "Preterm or LBW infants born at home should receive immediate KMC if they do not have danger signs, and should be transferred to a health-care facility if needed.  A binder may help to keep the infant ..."

---

### Kịch bản 4: Bé uống thuốc hạ sốt Hapacol 150mg lúc 8h sáng, giờ 11h bé lại nóng thì có uống tiếp được không?
* **Từ khóa mong đợi**: `['Hapacol', 'Paracetamol', 'liều', 'tiếng']`
* **Nội dung các phân mảnh truy xuất được (Top 3)**:
  1. "# Hướng dẫn chăm sóc trẻ sơ sinh 1. Trẻ quấy khóc có thể do đói, đầy hơi, tã bẩn, buồn ngủ hoặc quá tải cảm giác. 2. Liều dùng thuốc hạ sốt Hapacol (Paracetamol) cho trẻ em thông thường là 10-15 mg/kg..."
  2. "  Kèm theo thuốc điều trị đúng phác đồ (kháng sinh, hạ sốt ) theo chỉ định  của bác sĩ  Bổ sung vi chất theo khuyến cáo   Vitamin A (theo chương trình bổ sung quốc gia)   Kẽm giúp gi m thời gian ho..."
  3. "to recommend that either animal milk or  milk formula could be consumed in later  infancy (6–11 months). In contrast, children  12–23 months consume more food and  therefore can derive more of their n..."

---

### Kịch bản 5: Bé 6 tháng nặng 7.2kg, dài 66cm thì có đạt chuẩn WHO không trợ lý?
* **Từ khóa mong đợi**: `['WHO', 'cân nặng', 'tăng trưởng', 'chuẩn']`
* **Nội dung các phân mảnh truy xuất được (Top 3)**:
  1. "Dấu hiệu nặng cần đưa trẻ đi bệnh viện ngay.   Thở nhanh theo tuổi (dưới 2 tháng ≥ 60 lần/phút; 2–12 tháng ≥ 50; 1 –5 tuổi  ≥ 40)   Tím tái   Không uống được, bú rất kém hoặc bỏ bú   Co giật   Lơ..."
  2. "and, among girls, reduced reproductive  capacity (6). Inappropriate complementary  feeding can result in overweight, type 2  diabetes and disability in adulthood (7). The  first two years of life are ..."
  3. "WHO recommendations for   care of the preterm   or low-birth-weight infant..."

---

### Kịch bản 6: Lên thực đơn ăn dặm tuần đầu tiên cho bé bắt đầu tập ăn dặm từ ngày mai.
* **Từ khóa mong đợi**: `['ăn dặm', 'cháo rây', 'thực đơn', 'nhóm']`
* **Nội dung các phân mảnh truy xuất được (Top 3)**:
  1. "## Nguyên tắc khi bé đã được ghi nhận dị ứng với một loại thực phẩm cụ thể  - Tránh hoàn toàn thực phẩm đó và các sản phẩm chứa thành phần từ nó (đọc kỹ nhãn thành phần). - Không tự ý thử lại thực phẩ..."
  2. "## Độ tuổi giới thiệu thực phẩm dễ gây dị ứng  - Không có bằng chứng cho thấy trì hoãn giới thiệu các thực phẩm dễ gây dị ứng sau 6 tháng giúp phòng ngừa dị ứng — ngược lại, giới thiệu sớm (trong giai..."
  3. "## Viêm phổi / bệnh đường hô hấp cần dinh dưỡng tăng cường  - Trẻ mắc bệnh đường hô hấp (viêm phổi, viêm phế quản) thường tiêu hao năng lượng nhiều hơn bình thường trong khi lại dễ biếng ăn — cần chú ..."

---

