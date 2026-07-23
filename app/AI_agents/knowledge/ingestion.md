PDF -> Parse -> chunk -> contextualize -> embeding 
vectorindex , keywordindex , catalog , knowledge graph chay nen 

retrival retrival egnine -? plan gather -> acess -> back -> finalize 
hybrid retrival , graph retrival , suficiency checky -> ansewr + citations 
pdf ->VLM -> Sênnces-aware chunking -> Contexttual ẻnichment -> LLM thêm 1,2 câu định vị chunk 
search index 
ebed -> faiss index -> sqllite chunks , bm25 khi truy vấn -a. câtlaog theo facet



                         ┌────────────────────────────┐
                         │      Document Sources      │
                         │ PDF • DOCX • HTML • Image │
                         └─────────────┬──────────────┘
                                       │
                                       ▼
                            VLM / OCR / Parsing
                                       │
                                       ▼
                     Rule-based + LLM Post-processing
            (Clean OCR, Recover Markdown, Remove Noise)
                                       │
                                       ▼
                        Sentence-aware Chunking
           (Section-aware, Semantic Chunking, Sliding Window)
                                       │
                                       ▼
                          Contextual Enrichment
      ┌─────────────────────────────────────────────────────────┐
      │ • Document title                                        │
      │ • Chapter / Section                                     │
      │ • Parent heading                                        │
      │ • Keywords                                               │
      │ • Summary                                                │
      │ • LLM thêm 1–2 câu mô tả vị trí và nội dung chunk        │
      │ • Metadata (page, source, year, topic...)               │
      └─────────────────────────────────────────────────────────┘
                                       │
                                       ▼
                         Embedding Generation
                                       │
        ┌──────────────────────────────┼─────────────────────────────┐
        ▼                              ▼                             ▼
   Vector Index                  Keyword Index                  Knowledge Graph
 (FAISS/Qdrant/pgvector)        (BM25/Lucene)               (Neo4j/GraphRAG)
        │                              │                             │
        └──────────────┬───────────────┴──────────────┬──────────────┘
                       ▼                              ▼
                  Catalog / Metadata Index (SQLite/Postgres)
          (Document, section, tags, author, source, facet filters)
                                       │
──────────────────────────────────────────────────────────────────────────────
                           Query Time
──────────────────────────────────────────────────────────────────────────────

User Query
      │
      ▼
Rewrite / Planning
      │
      ▼
Retrieval Engine
      │
      ├──────── Hybrid Retrieval
      │          ├── Dense Search
      │          ├── BM25 Search
      │          └── Merge + Rerank
      │
      ├──────── Graph Retrieval
      │          └── Traverse entities & relationships
      │
      ├──────── Catalog Filter
      │          └── Source / Topic / Date / Chapter
      │
      ▼
Gather Evidence
      │
      ▼
Sufficiency Check
      │
      ├── Enough evidence?
      │      ├── YES → Continue
      │      └── NO  → Retrieve again / Expand search
      ▼
LLM Synthesis
      │
      ▼
Answer + Citations


Document
    │
    ▼
Sentence Splitter
    │
    ▼
Sentence-aware Chunking
    │
    ▼
Chunk Overlap
    │
    ▼
Contextual Prefix (LLM)
    │
    ▼
Embedding
1. Sentence Splitter

Thay vì cắt theo số ký tự (1000 ký tự/chunk), trước tiên chia theo câu.

Ví dụ:

S1
S2
S3
S4
S5
S6
S7
S8
2. Sentence-aware Chunking

Ghép nhiều câu thành một chunk.

Ví dụ:

Chunk 1

S1
S2
S3
S4

----------------

Chunk 2

S5
S6
S7
S8

Điều này tránh việc cắt giữa một câu.

3. Chunk Overlap

Giữ lại một phần của chunk trước.

Ví dụ:

Chunk 1

S1
S2
S3
S4

----------------

Chunk 2

S3
S4
S5
S6
S7

----------------

Chunk 3

S6
S7
S8
S9

Overlap thường khoảng 10–20% hoặc 1–3 câu.

Mục đích:

không mất ngữ cảnh
giảm lỗi khi thông tin nằm ở ranh giới hai chunk
4. Contextual Prefix

Đây là bước mới trong Contextual Retrieval.

Sau khi có chunk, dùng LLM thêm 1–2 câu mô tả ngữ cảnh.

Ví dụ chunk gốc:

WHO recommends Kangaroo Mother Care immediately after birth.

Sau contextual prefix:

Context:
This chunk comes from the WHO guideline "WHO recommendations for care of the preterm or low-birth-weight infant" (2022). It belongs to Chapter 3, Section A.1 "Kangaroo Mother Care" and describes recommendations for clinically stable preterm infants.

Content:
WHO recommends Kangaroo Mother Care immediately after birth...

Lưu ý: prefix này chỉ phục vụ embedding và retrieval. Khi trả lời người dùng, bạn thường chỉ hiển thị nội dung gốc, không cần hiển thị đoạn context được thêm vào.

Vì sao chunk "đứng độc lập"?

Nếu chỉ có:

Use donor human milk whenever mother's own milk is unavailable.

thì embedding không biết:

nói về trẻ sơ sinh hay người lớn?
tài liệu WHO hay AAP?
đang nói về dinh dưỡng hay thuốc?

Sau khi thêm prefix:

Document:
WHO recommendations for care of the preterm or low-birth-weight infant.

Chapter:
Evidence and recommendations.

Section:
Donor Human Milk.

Population:
Preterm infants.

Content:
Use donor human milk whenever mother's own milk is unavailable.

Thì mỗi chunk tự mang đủ ngữ cảnh, ngay cả khi tách khỏi tài liệu gốc.