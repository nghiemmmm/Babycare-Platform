Không dùng LLM cho mọi request. Chỉ dùng model mạnh khi thực sự cần reasoning 

api gateway : tầng http network + orchestrator 
xử lý : Authentication + Throttling + validation + tracing 

tối ưu chi phí : 
bộ router điều phối : nhận requesr -> phân loại request -> chọn execution -> gọi service tương ứng 
phân loại : Extract / Deterministic -> những request mà không cần AI suy luận 
-> xử lý database -> s3 -> results 
Ambiguous : câu hỏi không rõ ràng cần ngữ ngữ : 
RAG Pipeline
   ↓
Query Understanding
   ↓
Hybrid Search
   ├── BM25
   └── Vector Search
          ↓
       Reranker
          ↓
       Top-K
          ↓
         LLM
          ↓
       Answer
Execution path : rẻ nhất : phân loại chi phí : extract document id , keyword/semanticsearch , complex reasoning ( database + search + RAG + RAG + LLM )
routertree 
Apply ACL 
Context Compaction 
Top 30–50 chunks
       ↓
Remove duplicates
       ↓
Rerank
       ↓
Merge related chunks
       ↓
Preserve metadata
       ↓
Apply ACL
       ↓
Token budget
       ↓
Top 5–10 evidence