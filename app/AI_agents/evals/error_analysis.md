# 🔍 Error Bucket Analysis Report

Phân tích nhóm lỗi (Error Buckets) trên tổng số **12 truy vấn** thử nghiệm.

---

## 📊 Thống kê Phân bổ Error Buckets

| Group Error Bucket | Số lượng Query | Tỷ lệ Phần trăm (%) | Mô tả & Hướng xử lý |
| :--- | :---: | :---: | :--- |
| **1. NO_ANSWER_IN_CORPUS** | `0` | `0.0%` | Truy vấn nằm ngoài scope kiến thức -> Abstention |
| **2. ANSWER_NOT_IN_TOP_50** | `6` | `50.0%` | Thiếu dữ liệu hoặc Embeddings không match |
| **3. ANSWER_IN_TOP_50_NOT_TOP_3** | `0` | `0.0%` | Cần Reranker hoặc tuning RRF weights |
| **4. ANSWER_IN_TOP_3** | `0` | `0.0%` | Tài liệu chính xác nằm ở Rank 2 hoặc 3 |
| **5. ANSWER_AT_RANK_1** | `6` | `50.0%` | Tìm kiếm chính xác tuyệt đối ngay vị trí đầu tiên |
| **6. FILTERED_BY_THRESHOLD** | `0` | `0.0%` | Bị loại bởi ngưỡng lọc điểm số L2/Cosine |
