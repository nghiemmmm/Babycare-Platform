# Kiến trúc Tối ưu hóa Toàn diện Luồng RAG (RAG Optimizer Guide)

Tài liệu này tổng hợp toàn bộ các kỹ thuật tối ưu hóa trong hệ thống **RAG (Retrieval-Augmented Generation)** của BabyCare AI, bao gồm cả 4 giai đoạn: **Pre-Retrieval (Query Optimization)**, **Retrieval (Hybrid & MMR Diversity)**, **Post-Retrieval (RRF, Rerank & Compaction)**, và **Context Ordering (Prompt Assembling)**.

---

## 1. Sơ đồ Kiến trúc Tổng thể (End-to-End RAG Pipeline)

```
                            User Query
                                │
                                ▼
                   ┌───────────────────────────┐
                   │   RAG Trigger Evaluator   │ ──(Chitchat / Personal DB)──► Bypass RAG (0ms)
                   └─────────────┬─────────────┘
                                 │ (Cần tri thức y tế / WHO)
                                 ▼
                   ┌───────────────────────────┐
                   │    RAGCacheManager (LRU)  │ ──(Cache Hit < 5ms)─────────► Trả về Context
                   └─────────────┬─────────────┘
                                 │ (Cache Miss)
                                 ▼
                   ┌───────────────────────────┐
                   │      Query Analyzer       │
                   └─────────────┬─────────────┘
                    ┌────────────┴────────────┐
                    ▼                         ▼
         Fast-Path Pure Python      LLM Deep Analysis (Gemini Flash)
         (Câu hỏi ngắn < 15 từ)     (Câu hỏi phức tạp, đa triệu chứng)
                    └────────────┬────────────┘
                                 ▼
                        ┌─────────────────┐
                        │   SearchPlan    │
                        └────────┬────────┘
                                 │
           ┌─────────────────────┴─────────────────────┐
           ▼                                           ▼
┌──────────────────────┐                   ┌──────────────────────┐
│  FAISS Dense Search  │                   │  BM25 Sparse Search  │
│  (BGE-M3 Embeddings) │                   │  (Keywords Tiếng Việt)│
│  + MMR Diversity     │                   │                      │
└──────────┬───────────┘                   └──────────┬───────────┘
           │ (Top 10 candidates)                      │ (Top 10 candidates)
           └─────────────────────┬─────────────────────┘
                                 ▼
                   ┌───────────────────────────┐
                   │ Reciprocal Rank Fusion    │
                   │ (RRF = sum(1 / (60+rank)) │
                   └─────────────┬─────────────┘
                                 │
                                 ▼
                   ┌───────────────────────────┐
                   │  Local Cross-Encoder      │
                   │  (mxbai-rerank-xsmall-v1) │ ──(Top 6 candidates, CPU < 350 chars)
                   └─────────────┬─────────────┘
                                 │
                                 ▼
                   ┌───────────────────────────┐
                   │    Context Compressor     │
                   │  • Deduplication          │
                   │  • Merge related chunks   │
                   │  • Token Budget (800 tok) │
                   └─────────────┬─────────────┘
                                 │
                                 ▼
                   ┌───────────────────────────┐
                   │   RAG Cache Store &       │
                   │   Context Builder (Order) │
                   └───────────────────────────┘
```

---

## 2. Pre-Retrieval: Tối ưu hóa Truy vấn (Query Optimization)

### 2.1. RAG Gating / Trigger Bypass (`rag_trigger.py`)
- **Chitchat Bypass**: Các câu chào hỏi, cảm ơn (`"xin chào"`, `"cảm ơn"`, `< 15` ký tự) $\rightarrow$ Không gọi RAG.
- **Personal Profile Bypass**: Các câu hỏi tra cứu dữ liệu cá nhân ngắn (`< 40` ký tự như *"bé sinh ngày nào"*, *"bé nặng bao nhiêu"*) $\rightarrow$ Chuyển thẳng sang truy vấn Database (Firestore), không tốn tài nguyên RAG.
- **Knowledge Required**: Kích hoạt khi phát hiện từ khóa y khoa, thuốc, liều dùng, tiêu chuẩn WHO, dị ứng hoặc câu hỏi dài > 25 ký tự.

### 2.2. Định tuyến truy vấn 2 chế độ (`query_analyzer.py`)
- **Fast-Path Pure Python (< 0.1ms, 0 Token LLM)**: 
  - Áp dụng cho câu hỏi ngắn, trực diện (`< 15 từ`, `< 150 ký tự`).
  - Lọc stop words tiếng Việt (`cần`, `cho`, `với`, `mỗi`, `ngày`...).
  - Gán bộ lọc `category: 'health'` hoặc `category: 'nutrition'`.
- **LLM Deep Semantic Analysis**:
  - Dành cho câu hỏi phức tạp, mơ hồ, nhiều triệu chứng (*"dạo này bé lười ăn kèm đi ngoài phân sống có sao không?"*).
  - Sử dụng Gemini Flash Structured Output để trích xuất `SearchPlan`:
    - `keywords`: 2-5 từ khóa chọn lọc riêng cho **BM25 Sparse Search**.
    - `dense_query`: Viết lại câu hỏi đầy đủ ngữ nghĩa y khoa chuẩn xác riêng cho **FAISS Dense Search**.
    - `filters`: Bộ lọc metadata tương ứng.

---

## 3. Retrieval: Hybrid Search & MMR Semantic Diversity

### 3.1. Truy vấn chuyên biệt hóa (Specialized Hybrid Search)
- **Kênh Sparse (BM25)**: Nhận `plan.keywords` đã lọc sạch stopwords để khớp chính xác tên thuốc, biệt dược, triệu chứng.
- **Kênh Dense (FAISS)**: Nhận `plan.dense_query` (chuẩn hóa ngữ nghĩa) đi qua model local `BAAI/bge-m3` (dimension 1024).

### 3.2. MMR (Maximal Marginal Relevance) - Đa dạng hóa Ngữ nghĩa
- **Vấn đề**: Tránh việc top kết quả bị chiếm trọn bởi các chunk diễn đạt cùng 1 ý (ví dụ: 3 chunk cùng nói về liều Paracetamol).
- **Công thức**:
  $$\text{MMR} = \arg\max_{d_i \in R \setminus S} \Big[ \lambda \cdot \text{Sim}(d_i, Q) - (1 - \lambda) \cdot \max_{d_j \in S} \text{Sim}(d_i, d_j) \Big]$$
- **Cấu hình chuẩn trong `constant.py`**:
  - `RAG_ENABLE_MMR = True`
  - `RAG_MMR_LAMBDA = 0.7` (70% ưu tiên độ liên quan + 30% ưu tiên độ đa dạng)
  - `RAG_MMR_FETCH_K_MULTIPLIER = 3` (Quét trước 30 ứng viên để tính toán MMR trước khi lọc về 10 ứng viên)

---

## 4. Post-Retrieval: Tái xếp hạng & Nén ngữ cảnh

### 4.1. Hợp nhất Xếp hạng RRF (Reciprocal Rank Fusion)
- Công thức: $\text{RRF\_Score}(d) = \sum \frac{1}{60 + \text{rank}(d)}$.
- Hợp nhất kết quả từ FAISS và BM25 mà không bị phụ thuộc vào thang điểm số khác nhau.

### 4.2. Local Cross-Encoder Re-ranking (`reranker.py`)
- Model: `mixedbread-ai/mxbai-rerank-xsmall-v1` chạy local CPU.
- **Tối ưu hóa CPU Latency**:
  - Chỉ rerank Top 6 candidates từ RRF.
  - Cắt ngắn văn bản xuống 350 ký tự đầu (`doc.page_content[:350]`) để giảm độ phức tạp tự chú ý $O(N^2)$ $\rightarrow$ **Tăng tốc ~10-20 lần**.
  - Thực thi dưới `torch.inference_mode()`.

### 4.3. Nén ngữ cảnh & Kiểm soát Token Budget (`context_compressor.py`)
1. **Deduplication**: Khử trùng lặp nội dung dựa trên fingerprint 150 ký tự đầu.
2. **Merge Related Chunks**: Gom các chunk cùng tài liệu gốc, giữ nguyên nguồn, chương mục và số trang:
   ```text
   --- Tài liệu 1 (Nguồn: Hướng dẫn ăn dặm | Trang: 12, 14 | Mục: Chế độ đạm) ---
   [Nội dung đoạn 1]
   ---
   [Nội dung đoạn 2]
   ```
3. **Token Budget Guard**: Áp trần cố định `RAG_MAX_TOKENS = 800`, tự động cắt tỉa gọn gàng nếu vượt ngưỡng.

---

## 5. Context Ordering: Chống hiện tượng "Lost in the Middle"

Triển khai tại [`ContextBuilder`](file:///d:/ViT/BABYCARE/babycare-ai/app/AI_agents/context/context_builder.py):

| Vị trí | Nguồn (`ContextSource`) | Priority | Vị trí trong Prompt | Rationale |
| :---: | :--- | :---: | :--- | :--- |
| **1** | `SYSTEM_INSTRUCTION` + `BABY_PROFILE` | **100** | **Đầu prompt (Primacy)** | Định hình persona chuyên gia & thông số định danh bé |
| **2** | `LONG_TERM_MEMORY` (Facts) | **85** | Ngay sau Hồ sơ | Tiền sử bệnh, dị ứng (không bao giờ được bỏ qua) |
| **3** | `RAG_DOCS` (Tri thức WHO) | **70** | Cuối phần System Instruction | Tài liệu y khoa tham chiếu kèm yêu cầu dẫn nguồn |
| **4** | `CONVERSATION_SUMMARY` | **60** | Giữa phần System Instruction | Tóm tắt các phiên trò chuyện trước |
| **5** | `RECENT_MESSAGES` | **50** | Phần `messages` | Lịch sử chat gần nhất, cấp phát token động |
| **6** | `USER_QUERY` | **100** | **Cuối cùng (Recency)** | Trọng tâm câu hỏi cần trả lời ngay lập tức |

---

## 6. Bộ nhớ đệm In-Memory 24h (`rag_cache.py`)

- Key đệm: `f"{query}_{k}_{domain}_{max_tokens}"`
- Cơ chế: In-Memory LRU Cache (OrderedDict, tối đa 500 entries, TTL 24h).
- **Hiệu quả**: Trả kết quả trong **< 5ms**, tiết kiệm 100% chi phí CPU/Embedding/LLM khi người dùng hỏi lại các câu hỏi phổ biến.
