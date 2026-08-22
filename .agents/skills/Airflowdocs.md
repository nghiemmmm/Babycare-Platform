ây dựng một pipeline tự động lấy tài liệu → xử lý → tạo vector embedding → lưu vào vector database, để mỗi khi có dữ liệu mới hoặc cần cập nhật dữ liệu, hệ thống có thể chạy lại quy trình mà không phải làm thủ công.

Cụ thể từng thành phần:

Documents
   ↓
MinIO
   ↓
Apache Airflow
   ↓
Text extraction / Cleaning / Chunking
   ↓
Sentence Transformers
   ↓
Embedding vectors
   ↓
ChromaDB
   ↓
Vector Index
   ↓
RAG Retrieval
1. MinIO — lưu tài liệu gốc

Ví dụ bạn có:

company_policy.pdf
financial_report.pdf
product_manual.docx

Bạn lưu các file này vào MinIO.

MinIO đóng vai trò giống một object storage, nơi chứa dữ liệu gốc.

2. Apache Airflow — tự động hóa workflow

Thay vì mỗi lần có file mới lại phải chạy Python thủ công:

python ingest.py
python embed.py
python index.py

Airflow sẽ quản lý workflow:

Detect new documents
        ↓
Extract text
        ↓
Chunk documents
        ↓
Generate embeddings
        ↓
Store vectors

Ví dụ:

Every day at 02:00
        ↓
Airflow DAG chạy
        ↓
Lấy document mới từ MinIO
        ↓
Chunk
        ↓
Embedding
        ↓
Index vào ChromaDB
3. Sentence Transformers — biến text thành vector

Ví dụ:

"How can I reset my password?"

được biến thành một vector:

[0.12, -0.43, 0.87, ..., 0.21]

Vector này biểu diễn ngữ nghĩa của câu.

Sau đó có thể tìm các đoạn văn có ý nghĩa tương tự bằng vector similarity.

4. ChromaDB — lưu và tìm kiếm vector

ChromaDB lưu:

Document chunk
      +
Embedding vector
      +
Metadata

Ví dụ:

chunk:
"Employees must reset their password every 90 days."


embedding:
[0.12, -0.43, ...]


metadata:
{
    "source": "company_policy.pdf",
    "page": 12
}

Khi user hỏi:

"How often do I need to change my password?"

ChromaDB tìm những chunk có embedding gần với câu hỏi.

5. "Xử lý lặp lại nhiều nguồn dữ liệu một cách nhất quán" nghĩa là gì?

Đây là phần quan trọng nhất của câu CV.

Giả sử công ty có:

MinIO
 ├── HR/
 │    ├── policy.pdf
 │    └── handbook.pdf
 │
 ├── Finance/
 │    ├── report.pdf
 │    └── guideline.docx
 │
 └── Technical/
      ├── manual.pdf
      └── API.md

Thay vì xử lý từng file bằng tay, pipeline tự động áp dụng cùng một quy trình:

Document
   ↓
Extract
   ↓
Clean
   ↓
Chunk
   ↓
Embedding
   ↓
ChromaDB

Cho dù có:

10 tài liệu
1.000 tài liệu
10.000 tài liệu

thì workflow vẫn có thể được chạy lại theo cùng một logic.

Nói ngắn gọn

Câu đó thực chất là:

Tôi xây dựng một data pipeline cho RAG, tự động lấy tài liệu từ MinIO, xử lý/chia nhỏ tài liệu, tạo embedding bằng Sentence Transformers và indexing vào ChromaDB, với Airflow chịu trách nhiệm orchestration.

Nếu đi phỏng vấn, bạn nên hiểu nó theo 4 vai trò:

Công cụ	Vai trò
MinIO	Lưu document gốc
Airflow	Orchestrate/automate pipeline
Sentence Transformers	Text → embedding
ChromaDB	Lưu & vector search

Đây chính là ingestion/indexing pipeline của một hệ thống RAG.
Pipeline của họ:

Documents
   ↓
Local Parsing
   ↓
Citation-safe Chunks
   ↓
Local BGE Embedding
   ↓
PostgreSQL + pgvector
   +
Full-text Search
   ↓
RRF Hybrid Retrieval
   ↓
Optional BGE Reranker
   ↓
LLM

Các công cụ parsing họ sử dụng:

Docling
MarkItDown
Apache Tika

Embedding chạy on-box/local bằng các model BGE.
2. Cách tiếp cận được đánh giá cao nhất

Một commenter đưa ra kiến trúc tốt hơn:

                 ┌───────────────┐
PDF/PPT/DOCX ──→ │ Document Parse│
                 └───────┬───────┘
                         ↓
              Page-level Intermediate
                  Representation
                         ↓
        ┌────────────────┼────────────────┐
        ↓                ↓                ↓
      Text             Table           Figure
      Block             Block            Block
        │                │                │
        └────────────────┼────────────────┘
                         ↓
                  Quality Evaluation
                         ↓
                ┌────────┴────────┐
                │                 │
             PASS              LOW CONF
                │                 │
                ↓                 ↓
             Chunk            Quarantine /
                │              Re-parse
                ↓
            Embedding
                ↓
          Vector Database

Điểm quan trọng: không chunk trực tiếp từ output parser.

Thay vào đó:

Parser
  ↓
Page-level IR
  ↓
Quality Check
  ↓
Chunking

IR nên giữ:

text blocks
headings
tables
figures/images
page number
bounding boxes
reading order
header/footer
OCR confidence
document structure

Như vậy chunk luôn có thể trace ngược:

chunk
 ↓
block
 ↓
page
 ↓
original document
3. “Page-level warning” thực chất nên làm thế nào?

Đây là phần đáng học nhất.

Không nên chỉ có:

parser.parse(file)
# success

Mà mỗi page nên có một quality score:

Page 17
────────────────────────
OCR confidence       0.71
Text coverage        0.82
Table integrity      0.55
Reading order        0.91
Layout confidence    0.63


Overall              0.67
Status               ⚠ REVIEW

Sau đó đặt rule:

score >= 0.85
    → PASS


0.65 <= score < 0.85
    → WARNING


score < 0.65
    → QUARANTINE / RE-PARSE

Quan trọng hơn nữa: đừng chỉ dựa vào confidence mà parser tự báo.

Nên có các heuristic độc lập.

Ví dụ:

Text sanity
expected characters ≈ 5000
extracted characters = 320
→ suspicious
OCR garbage
"Th1s 1s a d0cument w1th..."

→ suspicious.

Reading-order problem

Ví dụ PDF có:

Column A       Column B


1              5
2              6
3              7
4              8

nhưng parser trả:

1 5 2 6 3 7 4 8

→ layout failure.

Table integrity

Original:

| Drug | Dose | Frequency |
|------|------|-----------|
| A    | 5mg  | BID       |

Parser:

Drug Dose Frequency A 5mg BID

→ mất cấu trúc bảng.

4. Đặc biệt quan trọng: đánh giá parser trước retrieval

Thread có một ý rất đúng:

page-level eval harness trước khi chọn parser.

Tức là đừng làm:

Parser A → RAG evaluation
Parser B → RAG evaluation

mà nên có:

                    ┌→ Parser A ─→ Parse Evaluation
Document → Gold Set ├→ Parser B ─→ Parse Evaluation
                    └→ Parser C ─→ Parse Evaluation

Gold set phải chứa những page khó, không phải document đẹp.

Ví dụ:

✓ scanned PDF
✓ OCR
✓ multi-column
✓ rotated page
✓ complex table
✓ nested table
✓ figure
✓ caption
✓ formula
✓ handwriting
✓ form
✓ signature
✓ PowerPoint export
✓ appendix
✓ header/footer

Đây mới là test thực tế.
 Asynchronous BullMQ + Redis
 Xây dựng hệ thống xử lý tài liệu chạy nền bằng BullMQ + Redis, để các tác vụ nặng như đọc PDF → chia nhỏ nội dung → tạo embedding → lưu vector không làm người dùng phải chờ trong request.

Flow đơn giản

User upload PDF
→ API nhận file ngay
→ Đẩy job vào Redis/BullMQ
→ Worker xử lý nền:
PDF Parsing → Chunking → Embedding → Vector Indexing
→ Hoàn thành → cập nhật trạng thái.

Ý nghĩa

Thay vì:

User → Upload → xử lý toàn bộ PDF → chờ → Response

thì chuyển thành:

User → Upload → Queue Job → Response ngay
　　　　　　　　　　　↓
　　　　　　　Background Worker
　　　　　　　PDF → Chunk → Embedding → Vector DB

Điểm quan trọng nhất:
👉 Tách document ingestion khỏi request-response cycle bằng asynchronous job queue, giúp API không bị block khi xử lý tài liệu lớn.