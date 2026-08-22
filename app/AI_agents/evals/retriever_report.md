# Báo cáo Đánh giá Chất lượng Bộ truy xuất (Retriever Evaluation Report)

Báo cáo này tập trung đánh giá chất lượng của **MedicalRetriever (FAISS + BAAI/bge-m3)** sau khi đã tối ưu hóa kích thước phân mảnh (1500 ký tự).

---

## 📊 Chỉ số trung bình của Bộ truy xuất (Average Metrics)
* **Mean Hit@3**: `0.43` (Khả năng tìm thấy từ khóa chuẩn trong Top 3 tài liệu)
* **MRR (Mean Reciprocal Rank)**: `0.43` (Xếp hạng nghịch đảo trung bình của kết quả đúng đầu tiên)
* **Recall@5**: `0.17` (Độ phủ của từ khóa trong Top 5 tài liệu)
* **Context Precision (Độ chính xác ngữ cảnh)**: `0.14 / 1.0` (Tỷ lệ phân mảnh thực sự hữu ích được sắp xếp ở vị trí cao)
* **Context Recall (Độ phủ ngữ cảnh)**: `0.12 / 1.0` (Khả năng bao phủ các thông tin mong đợi so với Ground Truth)

---

## 📝 Chi tiết đánh giá từng kịch bản RAG

| ID | Câu hỏi | Từ khóa mong đợi | Hit@3 | MRR | Recall@5 | Context Precision | Context Recall |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| 1 | Chào trợ lý, tôi cần một vài lời khuyên về cách rèn bé sơ sinh tự ngủ. | `['tự ngủ', 'sơ sinh', 'rèn ngủ']` | `1.00` | `1.00` | `0.33` | `0.00` | `0.00` |
| 2 | Bé mấy tháng tuổi thì có thể bắt đầu tập ngồi được vậy bạn? | `['tập ngồi', 'mấy tháng']` | `0.00` | `0.00` | `0.00` | `0.00` | `0.00` |
| 3 | Phân tích giúp tôi file âm thanh tiếng khóc hungry_cry_baby.wav vừa tải lên. | `['tiếng khóc đói', 'hungry cry']` | `0.00` | `0.00` | `0.00` | `0.00` | `0.33` |
| 4 | Bé Bo nhà tôi bị sốt nóng đầu, cặp nhiệt độ thấy 38.8 độ C thì phải làm sao? | `['sốt trẻ em', '38.8 độ', 'hạ sốt']` | `1.00` | `1.00` | `0.33` | `0.00` | `0.17` |
| 5 | Bé uống thuốc hạ sốt Hapacol 150mg lúc 8h sáng, giờ 11h bé lại nóng thì có uống tiếp được không? | `['khoảng cách liều', 'hạ sốt']` | `1.00` | `1.00` | `0.50` | `1.00` | `0.33` |
| 6 | Bé 6 tháng nặng 7.2kg, dài 66cm thì có đạt chuẩn WHO không trợ lý? | `['chuẩn tăng trưởng WHO', '6 tháng tuổi']` | `0.00` | `0.00` | `0.00` | `0.00` | `0.00` |
| 7 | Lên thực đơn ăn dặm tuần đầu tiên cho bé bắt đầu tập ăn dặm từ ngày mai. | `['ăn dặm tuần đầu', 'cháo rây']` | `0.00` | `0.00` | `0.00` | `0.00` | `0.00` |

## 🔍 Nhật ký giải thích chi tiết từ Giám khảo

### Kịch bản 1: Chào trợ lý, tôi cần một vài lời khuyên về cách rèn bé sơ sinh tự ngủ.
* **Chi tiết Context Precision**: Chunk 1: Khong hop le (The chunk provides general newborn care tips such as reasons for crying, medication dosage, signs of hunger, and handling colic, but it does not offer any advice or methods for training a newborn to sleep independently.)
* **Chi tiết Context Recall**: Score: `0.00` - *The retrieved context does not contain any information about sleep training methods (EASY, CIO, Fading) or recommendations for creating a dark and quiet sleep environment, which were the core points of the expected notes.*

---

### Kịch bản 2: Bé mấy tháng tuổi thì có thể bắt đầu tập ngồi được vậy bạn?
* **Chi tiết Context Precision**: Chunk 1: Khong hop le (The chunk provides information on reasons for crying, medication dosage, signs of hunger, and handling colic, but does not contain any information about the age at which a baby can start sitting.)
* **Chi tiết Context Recall**: Score: `0.00` - *The retrieved context discusses reasons for crying, medication dosage, signs of hunger, and colic treatment, none of which are related to the expected notes about babies learning to sit, age ranges, readiness signs, or warnings against forcing them.*

---

### Kịch bản 3: Phân tích giúp tôi file âm thanh tiếng khóc hungry_cry_baby.wav vừa tải lên.
* **Chi tiết Context Precision**: Chunk 1: Khong hop le (The user's query asks for an analysis of a specific audio file ('hungry_cry_baby.wav'). The chunk provides general information about reasons for infant crying and care tips, but it does not perform any analysis of an audio file.)
* **Chi tiết Context Recall**: Score: `0.33` - *The context identifies hunger as a reason for crying and lists hunger signs, covering the first point. However, it completely misses the instructions to check the last feeding time and to play soothing music.*

---

### Kịch bản 4: Bé Bo nhà tôi bị sốt nóng đầu, cặp nhiệt độ thấy 38.8 độ C thì phải làm sao?
* **Chi tiết Context Precision**: Chunk 1: Khong hop le (Evaluation error: Error calling model 'gemini-2.5-flash' (RESOURCE_EXHAUSTED): 429 RESOURCE_EXHAUSTED. {'error': {'code': 429, 'message': 'You exceeded your current quota, please check your plan and billing details. For more information on this error, head to: https://ai.google.dev/gemini-api/docs/rate-limits. To monitor your current usage, head to: https://ai.dev/rate-limit. \n* Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_requests, limit: 5, model: gemini-2.5-flash\nPlease retry in 47.399816343s.', 'status': 'RESOURCE_EXHAUSTED', 'details': [{'@type': 'type.googleapis.com/google.rpc.Help', 'links': [{'description': 'Learn more about Gemini API quotas', 'url': 'https://ai.google.dev/gemini-api/docs/rate-limits'}]}, {'@type': 'type.googleapis.com/google.rpc.QuotaFailure', 'violations': [{'quotaMetric': 'generativelanguage.googleapis.com/generate_content_free_tier_requests', 'quotaId': 'GenerateRequestsPerMinutePerProjectPerModel-FreeTier', 'quotaDimensions': {'model': 'gemini-2.5-flash', 'location': 'global'}, 'quotaValue': '5'}]}, {'@type': 'type.googleapis.com/google.rpc.RetryInfo', 'retryDelay': '47s'}]}})
* **Chi tiết Context Recall**: Score: `0.17` - *The context only covers the dosage for Paracetamol. It misses instructions on warm compress, wearing loose clothing, warnings about taking the child to the hospital for continuous high fever or lethargy, and the mention of specialized medical advice.*

---

### Kịch bản 5: Bé uống thuốc hạ sốt Hapacol 150mg lúc 8h sáng, giờ 11h bé lại nóng thì có uống tiếp được không?
* **Chi tiết Context Precision**: Chunk 1: Hop le (The chunk provides information on the recommended interval for administering Hapacol (Paracetamol) for children ('cách mỗi 4-6 tiếng nếu sốt lại'), which directly answers the user's question about whether they can give another dose at 11h AM after the first dose at 8h AM.)
* **Chi tiết Context Recall**: Score: `0.33` - *The context only covers the recommended interval for Paracetamol/Hapacol (4-6 hours). It misses the specific warning about the 3-hour interval, the risk of liver toxicity, and the recommendation for warm compresses and close monitoring.*

---

### Kịch bản 6: Bé 6 tháng nặng 7.2kg, dài 66cm thì có đạt chuẩn WHO không trợ lý?
* **Chi tiết Context Precision**: Chunk 1: Khong hop le (Evaluation error: Error calling model 'gemini-2.5-flash' (UNAUTHENTICATED): 401 UNAUTHENTICATED. {'error': {'code': 401, 'message': 'Request had invalid authentication credentials. Expected OAuth 2 access token, login cookie or other valid authentication credential. See https://developers.google.com/identity/sign-in/web/devconsole-project.', 'status': 'UNAUTHENTICATED', 'details': [{'@type': 'type.googleapis.com/google.rpc.ErrorInfo', 'reason': 'ACCESS_TOKEN_TYPE_UNSUPPORTED', 'metadata': {'service': 'generativelanguage.googleapis.com', 'method': 'google.ai.generativelanguage.v1beta.GenerativeService.GenerateContent'}}]}})
* **Chi tiết Context Recall**: Score: `0.00` - *Evaluation error: Error calling model 'gemini-2.5-flash' (UNAUTHENTICATED): 401 UNAUTHENTICATED. {'error': {'code': 401, 'message': 'Request had invalid authentication credentials. Expected OAuth 2 access token, login cookie or other valid authentication credential. See https://developers.google.com/identity/sign-in/web/devconsole-project.', 'status': 'UNAUTHENTICATED', 'details': [{'@type': 'type.googleapis.com/google.rpc.ErrorInfo', 'reason': 'ACCESS_TOKEN_TYPE_UNSUPPORTED', 'metadata': {'method': 'google.ai.generativelanguage.v1beta.GenerativeService.GenerateContent', 'service': 'generativelanguage.googleapis.com'}}]}}*

---

### Kịch bản 7: Lên thực đơn ăn dặm tuần đầu tiên cho bé bắt đầu tập ăn dặm từ ngày mai.
* **Chi tiết Context Precision**: Chunk 1: Khong hop le (Evaluation error: Error calling model 'gemini-2.5-flash' (UNAUTHENTICATED): 401 UNAUTHENTICATED. {'error': {'code': 401, 'message': 'Request had invalid authentication credentials. Expected OAuth 2 access token, login cookie or other valid authentication credential. See https://developers.google.com/identity/sign-in/web/devconsole-project.', 'status': 'UNAUTHENTICATED', 'details': [{'@type': 'type.googleapis.com/google.rpc.ErrorInfo', 'reason': 'ACCESS_TOKEN_TYPE_UNSUPPORTED', 'metadata': {'service': 'generativelanguage.googleapis.com', 'method': 'google.ai.generativelanguage.v1beta.GenerativeService.GenerateContent'}}]}})
* **Chi tiết Context Recall**: Score: `0.00` - *Evaluation error: Error calling model 'gemini-2.5-flash' (UNAUTHENTICATED): 401 UNAUTHENTICATED. {'error': {'code': 401, 'message': 'Request had invalid authentication credentials. Expected OAuth 2 access token, login cookie or other valid authentication credential. See https://developers.google.com/identity/sign-in/web/devconsole-project.', 'status': 'UNAUTHENTICATED', 'details': [{'@type': 'type.googleapis.com/google.rpc.ErrorInfo', 'reason': 'ACCESS_TOKEN_TYPE_UNSUPPORTED', 'metadata': {'method': 'google.ai.generativelanguage.v1beta.GenerativeService.GenerateContent', 'service': 'generativelanguage.googleapis.com'}}]}}*

---

