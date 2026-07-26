# Báo cáo Đánh giá Bộ truy xuất Cục bộ (Local Retriever Evaluation Report)

Báo cáo này đánh giá chất lượng của **MedicalRetriever (FAISS + BAAI/bge-m3)** cục bộ bằng các chỉ số định lượng toán học (không dùng LLM-as-a-Judge) để tiết kiệm chi phí API.

---

## 📊 Chỉ số Trung bình Hệ thống (Average Metrics)
* **Mean Hit@1**: `0.50` (Tỷ lệ tìm thấy từ khóa chuẩn trong kết quả đầu tiên)
* **Mean Hit@3**: `0.83` (Tỷ lệ tìm thấy từ khóa chuẩn trong Top 3)
* **Mean Hit@5**: `1.00` (Tỷ lệ tìm thấy từ khóa chuẩn trong Top 5)
* **MRR (Mean Reciprocal Rank)**: `0.68` (Xếp hạng nghịch đảo trung bình của kết quả khớp từ khóa đầu tiên)
* **Mean Recall@3**: `0.54` (Độ phủ của từ khóa trong Top 3 tài liệu)
* **Mean Recall@5**: `0.67` (Độ phủ của từ khóa trong Top 5 tài liệu)

---

## 📝 Chi tiết Đánh giá Từng Kịch bản

| ID | Câu hỏi của Phụ huynh | Từ khóa mong đợi | Hit@1 | Hit@3 | Hit@5 | MRR | Recall@3 | Recall@5 |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| 1 | Chao tro ly, toi can mot vai loi khuyen ve cach ren be so sinh tu ngu. | `['infant', 'skin-to-skin', 'sleep', 'preterm']` | `0.00` | `1.00` | `1.00` | `0.50` | `0.50` | `0.75` |
| 2 | Be may thang tuoi thi co the bat dau tap ngoi duoc vay ban? | `['cognitive', 'development', 'months', 'infant']` | `1.00` | `1.00` | `1.00` | `1.00` | `0.50` | `0.50` |
| 3 | Be Bo nha toi bi sot nong dau, cap nhiet do thay 38.8 do C thi phai lam sao? | `['temperature', 'fever', 'danger', 'health']` | `1.00` | `1.00` | `1.00` | `1.00` | `0.75` | `0.75` |
| 4 | Be uong thuoc ha sot Hapacol 150mg luc 8h sang, gio 11h be lai nong thi co uong tiep duoc khong? | `['temperature', 'health', 'care', 'infant']` | `0.00` | `1.00` | `1.00` | `0.33` | `0.75` | `0.75` |
| 5 | Be 6 thang nang 7.2kg, dai 66cm thi co dat chuan WHO khong tro ly? | `['WHO', 'weight', 'birth', 'growth']` | `1.00` | `1.00` | `1.00` | `1.00` | `0.75` | `0.75` |
| 6 | Len thuc don an dam tuan dau tien cho be bat dau tap an dam tu ngay mai. | `['complementary', 'feeding', 'food', 'months']` | `0.00` | `0.00` | `1.00` | `0.25` | `0.00` | `0.50` |

## 🔍 Nhật ký Nội dung Truy xuất chi tiết (Top 3 Chunks)

### Kịch bản 1: Chao tro ly, toi can mot vai loi khuyen ve cach ren be so sinh tu ngu.
* **Từ khóa mong đợi**: `['infant', 'skin-to-skin', 'sleep', 'preterm']`
* **Nội dung các phân mảnh truy xuất được (Top 3)**:
  1. "Trẻ quấy khóc có thể do đói hoặc tã bẩn...."
  2. "  Very-low-certainty evidence from three trials totalling 342 participants suggests a decrease in duration of hospitalization (days to discharge) (MD -1.42, 95% CI -5.43 to 2.59).  The effect of gesta..."
  3. "  FAST AND SLOW ADVANCEMENT OF FEEDING RECOMMENDATION A.8 (UPDATED) In preterm or low-birth-weight (LBW) infants, including very preterm (< 32 weeks' gestation) or very LBW (< 1.5 kg) infants, who nee..."

---

### Kịch bản 2: Be may thang tuoi thi co the bat dau tap ngoi duoc vay ban?
* **Từ khóa mong đợi**: `['cognitive', 'development', 'months', 'infant']`
* **Nội dung các phân mảnh truy xuất được (Top 3)**:
  1. "  This includes the Guideline Development Group (GDG), which was responsible for making decisions about the content of the guideline based on evidence presented during meetings.  The GDG also reviewed..."
  2. "Trẻ quấy khóc có thể do đói hoặc tã bẩn...."
  3. "are correctwen, a language model from Alibaba Cloud. Specializing in providing information andGenerating a response...   Sentence  structure and content understanding and indexing as is, concise sente..."

---

### Kịch bản 3: Be Bo nha toi bi sot nong dau, cap nhiet do thay 38.8 do C thi phai lam sao?
* **Từ khóa mong đợi**: `['temperature', 'fever', 'danger', 'health']`
* **Nội dung các phân mảnh truy xuất được (Top 3)**:
  1. "  Preterm or LBW infants born at home should receive immediate KMC if they do not have danger signs, and should be transferred to a health-care facility if needed.  A binder may help to keep the infan..."
  2. "Trẻ quấy khóc có thể do đói hoặc tã bẩn...."
  3. "Sentence 1: This chunk belongs in the References section under Chapter 3, Evidence and Recommendations. Sentence 2: The topic summarizes the formatted references text, likely from an academic paper or..."

---

### Kịch bản 4: Be uong thuoc ha sot Hapacol 150mg luc 8h sang, gio 11h be lai nong thi co uong tiep duoc khong?
* **Từ khóa mong đợi**: `['temperature', 'health', 'care', 'infant']`
* **Nội dung các phân mảnh truy xuất được (Top 3)**:
  1. "Trẻ quấy khóc có thể do đói hoặc tã bẩn...."
  2. "  This includes the Guideline Development Group (GDG), which was responsible for making decisions about the content of the guideline based on evidence presented during meetings.  The GDG also reviewed..."
  3. "  Another synthesis of qualitative studies suggested that providing KMC can be restorative as well as energy-draining for mothers, fathers, and partners (37).  KMC can be implemented at home and at al..."

---

### Kịch bản 5: Be 6 thang nang 7.2kg, dai 66cm thi co dat chuan WHO khong tro ly?
* **Từ khóa mong đợi**: `['WHO', 'weight', 'birth', 'growth']`
* **Nội dung các phân mảnh truy xuất được (Top 3)**:
  1. "  - The GDG also considered that EBF until 6 months of age is the standard of care for preterm and LBW infants across many high-, middle- and low-income countries and is the foundation of many nationa..."
  2. "  This includes the Guideline Development Group (GDG), which was responsible for making decisions about the content of the guideline based on evidence presented during meetings.  The GDG also reviewed..."
  3. "  Additionally, moderate certainty evidence from five trials with 399 participants demonstrates improved head circumference gain (MD = 1.04 mm/week; 95% CI = 0.18 to 1.04).  #### Neurodevelopment Mode..."

---

### Kịch bản 6: Len thuc don an dam tuan dau tien cho be bat dau tap an dam tu ngay mai.
* **Từ khóa mong đợi**: `['complementary', 'feeding', 'food', 'months']`
* **Nội dung các phân mảnh truy xuất được (Top 3)**:
  1. "Evidence Type are correctwen, a language model from Alibaba. I specialize in providing precise and concise information.  Moreover, there was a noted decrease in the duration of hospital stays (MD -0.3..."
  2. "Trẻ quấy khóc có thể do đói hoặc tã bẩn...."
  3. "Sentence 1: This chunk belongs under the "Mortality" and "Growth" sections within the "Evidence and Recommendations" chapter. Sentence 2: The topic summarizes evidence on mortality, morbidity, and gro..."

---

