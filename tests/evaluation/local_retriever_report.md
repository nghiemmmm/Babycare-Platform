# Báo cáo Đánh giá Bộ truy xuất Cục bộ (Local Retriever Evaluation Report)

Báo cáo này đánh giá chất lượng của **MedicalRetriever (FAISS + BAAI/bge-m3)** cục bộ bằng các chỉ số định lượng toán học (không dùng LLM-as-a-Judge) để tiết kiệm chi phí API.

---

## 📊 Chỉ số Trung bình Hệ thống (Average Metrics)
* **Mean Hit@1**: `0.43` (Tỷ lệ tìm thấy từ khóa chuẩn trong kết quả đầu tiên)
* **Mean Hit@3**: `0.43` (Tỷ lệ tìm thấy từ khóa chuẩn trong Top 3)
* **Mean Hit@5**: `0.43` (Tỷ lệ tìm thấy từ khóa chuẩn trong Top 5)
* **MRR (Mean Reciprocal Rank)**: `0.43` (Xếp hạng nghịch đảo trung bình của kết quả khớp từ khóa đầu tiên)
* **Mean Recall@3**: `0.17` (Độ phủ của từ khóa trong Top 3 tài liệu)
* **Mean Recall@5**: `0.17` (Độ phủ của từ khóa trong Top 5 tài liệu)

---

## 📝 Chi tiết Đánh giá Từng Kịch bản

| ID | Câu hỏi của Phụ huynh | Từ khóa mong đợi | Hit@1 | Hit@3 | Hit@5 | MRR | Recall@3 | Recall@5 |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| 1 | Chào trợ lý, tôi cần một vài lời khuyên về cách rèn bé sơ sinh tự ngủ. | `['tự ngủ', 'sơ sinh', 'rèn ngủ']` | `1.00` | `1.00` | `1.00` | `1.00` | `0.33` | `0.33` |
| 2 | Bé mấy tháng tuổi thì có thể bắt đầu tập ngồi được vậy bạn? | `['tập ngồi', 'mấy tháng']` | `0.00` | `0.00` | `0.00` | `0.00` | `0.00` | `0.00` |
| 3 | Phân tích giúp tôi file âm thanh tiếng khóc hungry_cry_baby.wav vừa tải lên. | `['tiếng khóc đói', 'hungry cry']` | `0.00` | `0.00` | `0.00` | `0.00` | `0.00` | `0.00` |
| 4 | Bé Bo nhà tôi bị sốt nóng đầu, cặp nhiệt độ thấy 38.8 độ C thì phải làm sao? | `['sốt trẻ em', '38.8 độ', 'hạ sốt']` | `1.00` | `1.00` | `1.00` | `1.00` | `0.33` | `0.33` |
| 5 | Bé uống thuốc hạ sốt Hapacol 150mg lúc 8h sáng, giờ 11h bé lại nóng thì có uống tiếp được không? | `['khoảng cách liều', 'hạ sốt']` | `1.00` | `1.00` | `1.00` | `1.00` | `0.50` | `0.50` |
| 6 | Bé 6 tháng nặng 7.2kg, dài 66cm thì có đạt chuẩn WHO không trợ lý? | `['chuẩn tăng trưởng WHO', '6 tháng tuổi']` | `0.00` | `0.00` | `0.00` | `0.00` | `0.00` | `0.00` |
| 7 | Lên thực đơn ăn dặm tuần đầu tiên cho bé bắt đầu tập ăn dặm từ ngày mai. | `['ăn dặm tuần đầu', 'cháo rây']` | `0.00` | `0.00` | `0.00` | `0.00` | `0.00` | `0.00` |

## 🔍 Nhật ký Nội dung Truy xuất chi tiết (Top 3 Chunks)

### Kịch bản 1: Chào trợ lý, tôi cần một vài lời khuyên về cách rèn bé sơ sinh tự ngủ.
* **Từ khóa mong đợi**: `['tự ngủ', 'sơ sinh', 'rèn ngủ']`
* **Nội dung các phân mảnh truy xuất được (Top 3)**:
  1. "# Hướng dẫn chăm sóc trẻ sơ sinh 1. Trẻ quấy khóc có thể do đói, đầy hơi, tã bẩn, buồn ngủ hoặc quá tải cảm giác. 2. Liều dùng thuốc hạ sốt Hapacol (Paracetamol) cho trẻ em thông thường là 10-15 mg/kg..."
  2. "WHO recommendations on   maternal and newborn care for   a positive postnatal experience..."
  3. "WHO recommendations on  maternal and newborn care for   a positive postnatal experience..."

---

### Kịch bản 2: Bé mấy tháng tuổi thì có thể bắt đầu tập ngồi được vậy bạn?
* **Từ khóa mong đợi**: `['tập ngồi', 'mấy tháng']`
* **Nội dung các phân mảnh truy xuất được (Top 3)**:
  1. "# Hướng dẫn chăm sóc trẻ sơ sinh 1. Trẻ quấy khóc có thể do đói, đầy hơi, tã bẩn, buồn ngủ hoặc quá tải cảm giác. 2. Liều dùng thuốc hạ sốt Hapacol (Paracetamol) cho trẻ em thông thường là 10-15 mg/kg..."
  2. "WHO recommendations on   maternal and newborn care for   a positive postnatal experience..."
  3. "WHO recommendations on  maternal and newborn care for   a positive postnatal experience..."

---

### Kịch bản 3: Phân tích giúp tôi file âm thanh tiếng khóc hungry_cry_baby.wav vừa tải lên.
* **Từ khóa mong đợi**: `['tiếng khóc đói', 'hungry cry']`
* **Nội dung các phân mảnh truy xuất được (Top 3)**:
  1. "# Hướng dẫn chăm sóc trẻ sơ sinh 1. Trẻ quấy khóc có thể do đói, đầy hơi, tã bẩn, buồn ngủ hoặc quá tải cảm giác. 2. Liều dùng thuốc hạ sốt Hapacol (Paracetamol) cho trẻ em thông thường là 10-15 mg/kg..."
  2. "WHO recommendations on maternal and newborn care for a positive postnatal experience This publication is the update of the document published in 2014 entitled “WHO recommendations on postnatal  care o..."
  3. "USAID and the UNDP-UNFPA-UNICEF-WHO-World Bank Special Programme of Research, Development  and Research T raining in Human Reproduction (HRP), a cosponsored programme executed by the WHO,  funded this..."

---

### Kịch bản 4: Bé Bo nhà tôi bị sốt nóng đầu, cặp nhiệt độ thấy 38.8 độ C thì phải làm sao?
* **Từ khóa mong đợi**: `['sốt trẻ em', '38.8 độ', 'hạ sốt']`
* **Nội dung các phân mảnh truy xuất được (Top 3)**:
  1. "# Hướng dẫn chăm sóc trẻ sơ sinh 1. Trẻ quấy khóc có thể do đói, đầy hơi, tã bẩn, buồn ngủ hoặc quá tải cảm giác. 2. Liều dùng thuốc hạ sốt Hapacol (Paracetamol) cho trẻ em thông thường là 10-15 mg/kg..."
  2. "WHO recommendations on   maternal and newborn care for   a positive postnatal experience..."
  3. "WHO recommendations on  maternal and newborn care for   a positive postnatal experience..."

---

### Kịch bản 5: Bé uống thuốc hạ sốt Hapacol 150mg lúc 8h sáng, giờ 11h bé lại nóng thì có uống tiếp được không?
* **Từ khóa mong đợi**: `['khoảng cách liều', 'hạ sốt']`
* **Nội dung các phân mảnh truy xuất được (Top 3)**:
  1. "# Hướng dẫn chăm sóc trẻ sơ sinh 1. Trẻ quấy khóc có thể do đói, đầy hơi, tã bẩn, buồn ngủ hoặc quá tải cảm giác. 2. Liều dùng thuốc hạ sốt Hapacol (Paracetamol) cho trẻ em thông thường là 10-15 mg/kg..."
  2. "authentic edition”.  Any mediation relating to disputes arising under the licence shall be conducted in accordance with the mediation  rules of the World Intellectual Property Organization (http:/ /ww..."
  3. "WHO recommendations on maternal and newborn care for a positive postnatal experience This publication is the update of the document published in 2014 entitled “WHO recommendations on postnatal  care o..."

---

### Kịch bản 6: Bé 6 tháng nặng 7.2kg, dài 66cm thì có đạt chuẩn WHO không trợ lý?
* **Từ khóa mong đợi**: `['chuẩn tăng trưởng WHO', '6 tháng tuổi']`
* **Nội dung các phân mảnh truy xuất được (Top 3)**:
  1. "WHO recommendations on   maternal and newborn care for   a positive postnatal experience..."
  2. "WHO recommendations on  maternal and newborn care for   a positive postnatal experience..."
  3. "WHO recommendations on maternal and newborn care for a positive postnatal experience This publication is the update of the document published in 2014 entitled “WHO recommendations on postnatal  care o..."

---

### Kịch bản 7: Lên thực đơn ăn dặm tuần đầu tiên cho bé bắt đầu tập ăn dặm từ ngày mai.
* **Từ khóa mong đợi**: `['ăn dặm tuần đầu', 'cháo rây']`
* **Nội dung các phân mảnh truy xuất được (Top 3)**:
  1. "# Hướng dẫn chăm sóc trẻ sơ sinh 1. Trẻ quấy khóc có thể do đói, đầy hơi, tã bẩn, buồn ngủ hoặc quá tải cảm giác. 2. Liều dùng thuốc hạ sốt Hapacol (Paracetamol) cho trẻ em thông thường là 10-15 mg/kg..."
  2. "Contents Acknowledgements iv Acronyms and abbreviations v Executive summary vii 1. Intr oduction  1 2. Methods  3 3. E vidence and recommendations  12  A. Mat ernal care  13  B. Ne wborn care  9 7  C ..."
  3. "WHO recommendations on   maternal and newborn care for   a positive postnatal experience..."

---

