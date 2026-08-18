# 📊 Retrieval Ablation Experiment & Benchmark Report

Báo cáo thử nghiệm và đánh giá hệ thống **Information Retrieval (RAG)** cho **BabyCare AI**.

---

## 📈 Bảng So sánh Tổng hợp (Master Benchmark Table)

| Config | Hit@1 | Hit@3 | Hit@5 | Hit@10 | Hit@20 | MRR | Latency P50 | Latency P95 | Rerank Rate |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Dense (FAISS)** | `0.25` | **`0.33`** | `0.33` | `0.42` | `0.42` | `0.29` | **`832.4 ms`** | `13033.4 ms` | `0.0%` |
| **Dense + Threshold** | `0.25` | **`0.33`** | `0.33` | `0.42` | `0.42` | `0.29` | **`683.8 ms`** | `6148.6 ms` | `0.0%` |
| **Hybrid (Dense + BM25 RRF)** | `0.50` | **`0.50`** | `0.50` | `0.50` | `0.50` | `0.50` | **`813.0 ms`** | `5248.4 ms` | `0.0%` |
| **Dense + Reranker** | `0.33` | **`0.33`** | `0.33` | `0.33` | `0.33` | `0.33` | **`26284.2 ms`** | `71346.9 ms` | `100.0%` |
| **Hybrid + Reranker** | `0.42` | **`0.50`** | `0.50` | `0.50` | `0.50` | `0.46` | **`41117.8 ms`** | `70664.2 ms` | `100.0%` |
| **Hybrid + Selective Reranker** | `0.33` | **`0.50`** | `0.50` | `0.50` | `0.50` | `0.42` | **`0.0 ms`** | `1.5 ms` | `0.0%` |

---

## 🧪 Bootstrap Statistical Validation (95% CI)

- **So sánh**: Hybrid RRF vs Hybrid + Reranker
- **Mean Hit@3 Delta**: `+0.0000`
- **95% Confidence Interval**: `[+0.0000, +0.0000]`
- **Ý nghĩa Thống kê (Statistically Significant)**: `KHÔNG có ý nghĩa thống kê (Khoảng tin cậy chứa 0)`

---

## 💡 Production Recommendation

> **CASE A: Hybrid Dense + BM25 + RRF là Baseline Tối ưu nhất cho Production!**
> - **Hit@3**: `0.50` (đạt độ chính xác tối đa)
> - **MRR**: `0.50`
> - **Latency P50**: **`813.0 ms`** (Nhanh hơn gấp 6-10 lần so với khi qua Reranker trên CPU)
> - **Đề xuất Production**: Sử dụng **`Hybrid Dense + BM25 + RRF`** làm bộ truy xuất chính. Không cần bật CrossEncoder Reranker cho mọi truy vấn để đảm bảo tốc độ phản hồi real-time.
