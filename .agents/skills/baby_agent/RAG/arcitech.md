Đây là luồng xử lý được sắp xếp lại rõ ràng:

                    User
                      │
                      ▼
              Amazon API Gateway
      (Auth, Rate Limit, Validation, Tracing)
                      │
                      ▼
                 AWS Lambda Router
                      │
      ┌───────────────┴────────────────┐
      │                                │
      ▼                                ▼
 Deterministic Request          Ambiguous Request
      │                                │
      ▼                                ▼
 DynamoDB / S3                  Small Bedrock Model
      │                    (Intent + Keyword Extraction)
      ▼                                │
 Response                      OpenSearch Serverless
                               (Hybrid Retrieval)
                                      │
                           BM25 + Vector + Metadata + ACL
                                      │
                                      ▼
                               Top-K Documents
                                      │
                                      ▼
                           Lambda Context Compactor
                     (Rerank + Deduplicate + Token Budget)
                                      │
                  ┌───────────────────┴───────────────────┐
                  │                                       │
                  ▼                                       ▼
        Simple Question                         Complex Question
                  │                                       │
                  ▼                                       ▼
          Return Retrieved                  Large Bedrock Model
                                                (Synthesis)
                  └───────────────────┬───────────────────┘
                                      ▼
                              Response Formatter
                    (Citations + Cache + Streaming)
                                      │
                                      ▼
                                    User
Vì sao kiến trúc này tiết kiệm chi phí?

Thay vì mọi truy vấn đều gọi GPT-5 hoặc Claude, hệ thống phân tầng theo độ khó:

Loại truy vấn	Thành phần xử lý	Chi phí
"Mở tài liệu ABC"	Code + DynamoDB/S3	Gần như 0
"Tìm policy nghỉ phép"	Retrieval	Thấp
"So sánh chính sách nghỉ phép 2024 và 2025"	LLM tổng hợp	Cao

Ví dụ:

User:
"Link handbook"

↓

Lambda

↓

S3

↓

Done

Không cần LLM.

User:
"Vacation policy"

↓

Retriever

↓

Top 5 docs

↓

Return snippets

Chỉ cần retrieval.

User:
"How did the vacation policy change between 2023 and 2025?"

↓

Retriever

↓

Relevant docs

↓

LLM

↓

Summarize changes

Lúc này mới cần mô hình lớn.

Hybrid Retrieval

OpenSearch Serverless thực hiện nhiều chiến lược tìm kiếm cùng lúc:

Query
   │
   ├── BM25
   │
   ├── Dense Embedding
   │
   ├── Metadata Filter
   │
   └── ACL Filter

Sau đó hợp nhất kết quả.

Đây là cách nhiều hệ thống production triển khai vì:

BM25 tốt với từ khóa chính xác.
Vector Search hiểu ngữ nghĩa.
Metadata giảm nhiễu.
ACL đảm bảo chỉ truy xuất tài liệu người dùng được phép xem.
Context Compactor

Đây là thành phần nhiều người bỏ qua nhưng rất quan trọng.

Sau khi lấy Top-K tài liệu:

Top 20 Chunks
      │
      ▼
Remove duplicates
      │
      ▼
Rerank
      │
      ▼
Keep citations
      │
      ▼
Fit within token budget

Mục tiêu là giảm chi phí và tránh gửi quá nhiều ngữ cảnh vào LLM.

Các chỉ số cần đánh giá

Những tiêu chí trong bài rất sát với thực tế triển khai:

Metric	Ý nghĩa
Deterministic bypass rate	Bao nhiêu % truy vấn không cần LLM
ACL filtering	Không rò rỉ dữ liệu giữa người dùng/tenant
Top-K	Số tài liệu đưa vào tổng hợp
Token limit	Kiểm soát chi phí và độ trễ
Model routing	Điều hướng đúng mô hình theo độ khó
Cache hit	Tỷ lệ tận dụng kết quả đã có
Citation coverage	Câu trả lời có dẫn nguồn đầy đủ
Faithfulness	Có bịa thông tin không
Completeness	Trả lời đủ ý không
Scale-from-zero latency	Độ trễ khi Lambda cold start
So sánh với BabyCare AI

Nếu áp dụng vào BabyCare AI của bạn, kiến trúc có thể tương ứng như sau:

Enterprise Search	BabyCare AI
API Gateway	FastAPI Gateway + Authentication
Lambda Router	LangGraph Router / Intent Router
DynamoDB/S3	Firestore, PostgreSQL, Storage
Small Bedrock	Intent Classification Agent
OpenSearch Hybrid	Qdrant + BM25 + Metadata Retrieval
Context Compactor	Reranker + Context Builder + Token Budget
Large Bedrock	Health/Care Agent tổng hợp và giải thích
Response Formatter	Citation + Markdown + PDF Report
Có gì còn thiếu?

Đối với một hệ thống enterprise search ở quy mô lớn, mình sẽ bổ sung thêm một số thành phần:

Semantic cache để lưu câu trả lời cho các truy vấn tương tự, giảm số lần gọi LLM.
Cross-encoder reranker (ví dụ BGE Reranker hoặc Mixedbread) sau bước retrieval để cải thiện độ chính xác trước khi tổng hợp.
Query rewriting/decomposition cho các câu hỏi dài hoặc nhiều ý trước khi truy xuất.
Observability (OpenTelemetry, LangSmith, CloudWatch) để theo dõi route, chi phí, độ trễ và chất lượng.
Offline evaluation pipeline với bộ câu hỏi chuẩn để đo Recall@K, MRR, Faithfulness và Citation Accuracy sau mỗi lần cập nhật.

Đây là những thành phần thường thấy trong các hệ thống RAG production hiện đại và sẽ giúp kiến trúc không chỉ tiết kiệm chi phí mà còn duy trì chất lượng và khả năng mở rộng.