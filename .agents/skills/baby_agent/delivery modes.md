Bạn là Senior AI Systems Architect chuyên về:
- LLM application architecture
- FastAPI / Python backend
- Agentic AI
- RAG
- LangGraph
- asynchronous job processing
- SSE / streaming
- production-grade API design
- latency, throughput và UX

NHIỆM VỤ

Hãy audit toàn bộ source code của project hiện tại để đánh giá kiến trúc
AI Response Delivery của hệ thống.

Tập trung vào câu hỏi:

"Với cùng một AI model, hệ thống có đang lựa chọn đúng cách
giao kết quả cho client: SYNC, ASYNC hay STREAMING hay không?"

QUAN TRỌNG:
- KHÔNG sửa code ngay.
- KHÔNG refactor ngay.
- KHÔNG tự ý thay đổi architecture.
- Trước tiên phải đọc và hiểu implementation hiện tại.
- Nếu có vấn đề, phải chỉ rõ file, function/class và flow liên quan.
- Chỉ đề xuất thay đổi sau khi hoàn thành audit.

==================================================
1. PHÂN BIỆT 3 DELIVERY MODES
==================================================

Phân tích hệ thống theo 3 mode:

A. SYNC
Client gửi request và chờ toàn bộ response.

Phù hợp với:
- request nhanh
- authentication
- CRUD
- database lookup
- classification
- simple AI request có latency thấp

Flow:

Client
  ↓
HTTP Request
  ↓
Backend
  ↓
Model
  ↓
Complete Response
  ↓
Client


B. ASYNC / BACKGROUND

Client gửi job nhưng không block để chờ toàn bộ quá trình.

Flow:

Client
  ↓
POST /jobs
  ↓
Job accepted
  ↓
job_id
  ↓
Background Worker / Queue
  ↓
LLM / RAG / Agent
  ↓
Result
  ↓
Client lấy result sau hoặc nhận notification

Phù hợp với:
- batch document processing
- xử lý hàng nghìn tài liệu
- long-running agent
- report generation
- video/image processing
- embedding/indexing
- các task có thời gian xử lý dài


C. STREAMING

Model sinh kết quả đến đâu thì client nhận đến đó.

Ví dụ:
- SSE
- WebSocket
- HTTP streaming

Flow:

Client
  ↓
Request
  ↓
Backend
  ↓
LLM
  ↓
token/chunk/event
  ↓
Client UI
  ↓
token/chunk/event
  ↓
Client UI
  ↓
...

Phù hợp với:
- AI chatbot
- conversational assistant
- coding assistant
- interactive agent
- customer support
- long-form generation

==================================================
2. KHẢO SÁT TOÀN BỘ REQUEST FLOW
==================================================

Hãy tìm và phân tích:

- API endpoints
- FastAPI routes
- controllers
- services
- agents
- orchestrator
- LangGraph graph
- LLM invocation
- RAG pipeline
- background tasks
- task queues
- workers
- SSE
- WebSocket
- streaming generators
- polling
- job status APIs
- frontend API calls
- frontend streaming handlers

Tạo request flow cho từng loại request.

Ví dụ:

User
 ↓
Frontend
 ↓
POST /chat
 ↓
FastAPI
 ↓
AgentOrchestrator
 ↓
LangGraph
 ↓
RAG
 ↓
LLM
 ↓
Response

Sau đó xác định response được delivery theo:
SYNC / ASYNC / STREAMING


==================================================
3. TÌM CÁC ĐIỂM BLOCKING
==================================================

Tìm tất cả nơi có nguy cơ request bị block lâu.

Đặc biệt kiểm tra:

- synchronous LLM calls
- synchronous HTTP calls
- blocking database operations
- blocking RAG retrieval
- embedding generation
- reranking
- agent execution
- tool calls
- long-running loops
- file processing
- document parsing
- model inference

Phân loại:

SAFE:
< 100–300ms

MODERATE:
300ms–2s

LONG:
2–10s

VERY LONG:
> 10s

BATCH:
có thể kéo dài hàng phút/hàng giờ


==================================================
4. KIỂM TRA ASYNC THỰC SỰ HAY "ASYNC GIẢ"
==================================================

Không chỉ tìm từ khóa async/await.

Hãy kiểm tra implementation thực tế.

Ví dụ:

async def endpoint():
    result = blocking_function()
    return result

Đây KHÔNG phải asynchronous execution thực sự nếu
blocking_function() block event loop.

Kiểm tra:

- async def
- await
- asyncio
- FastAPI BackgroundTasks
- Celery
- Redis Queue
- Kafka
- RabbitMQ
- task queue
- worker process
- thread pool
- process pool

Phân biệt:

1. async I/O
2. background execution
3. parallel execution
4. job queue

Không được coi chúng là cùng một thứ.


==================================================
5. KIỂM TRA STREAMING
==================================================

Tìm xem hệ thống hiện tại có:

- StreamingResponse
- EventSourceResponse
- SSE
- WebSocket
- async generator
- yield
- stream=True
- token callbacks
- LangChain streaming
- LangGraph streaming
- frontend EventSource
- fetch streaming
- ReadableStream

hay không.

Nếu có, mô tả flow:

LLM
 ↓
callback / generator
 ↓
backend
 ↓
SSE
 ↓
frontend
 ↓
incremental UI


Kiểm tra xem streaming có thực sự token/chunk-level
hay chỉ trả một response lớn sau cùng.


==================================================
6. KIỂM TRA FRONTEND UX
==================================================

Audit frontend.

Xác định:

- request nào hiển thị loading
- request nào block UI
- request nào stream
- request nào polling
- request nào nhận job_id
- timeout hiện tại
- retry hiện tại
- cancellation
- abort request
- reconnect
- partial response handling

Đặc biệt kiểm tra:

Nếu AI mất 10 giây:

SYNC:
User phải nhìn loading 10 giây?

STREAMING:
User có nhận token đầu tiên sau 1 giây?

ASYNC:
User có thể rời khỏi màn hình và quay lại xem job?


==================================================
7. XÂY REQUEST → DELIVERY MATRIX
==================================================

Tạo bảng:

| Request | Current Mode | Recommended Mode | Latency | Blocking? | Reason |
|---------|--------------|------------------|---------|-----------|--------|

Ví dụ:

| Simple DB lookup | Sync | Sync | 50ms | No | Correct |
| Chat | Sync | Streaming | 5s | Yes | UX issue |
| Long report | Sync | Async | 60s | Yes | Architecture issue |
| Batch documents | Sync | Async | 30min | Yes | Critical |
| Short classification | Sync | Sync | 100ms | No | Correct |

Không được giả định.
Chỉ kết luận dựa trên source code.


==================================================
8. KIỂM TRA "ONE DELIVERY MODE FOR EVERYTHING"
==================================================

Xác định xem hệ thống có đang mắc lỗi:

"Mọi request đều POST → chờ LLM → trả JSON"

hay không.

Nếu có, đánh giá:

- latency
- timeout
- UX
- scalability
- concurrency
- resource utilization
- cost

Kiểm tra ngược lại:

Có phải mọi request đều bị stream dù không cần?

Có phải mọi request dài đều bị giữ HTTP connection?

Có phải batch job đang chạy trong request lifecycle?

Có phải frontend đang polling những thứ nên streaming?

Có phải streaming đang được dùng cho task phù hợp với async job?


==================================================
9. KIỂM TRA TIMEOUT VÀ FAILURE HANDLING
==================================================

Phân tích:

- API timeout
- reverse proxy timeout
- load balancer timeout
- LLM timeout
- database timeout
- retry
- cancellation
- client disconnect
- SSE disconnect
- worker failure
- job retry

Đặc biệt:

Nếu client disconnect trong lúc streaming:

Backend có tiếp tục chạy LLM không?

Nếu user đóng browser trong lúc long-running job:

Job có bị mất không?

Nếu worker crash:

Job có retry không?

Nếu request timeout:

LLM có tiếp tục chạy phía sau không?


==================================================
10. KIỂM TRA COST ARCHITECTURE
==================================================

Phân tích delivery mode ảnh hưởng đến:

- LLM token cost
- retry
- duplicate execution
- unnecessary inference
- concurrency
- worker utilization
- API connection duration

Ví dụ:

SYNC request timeout sau 30s nhưng LLM vẫn tiếp tục chạy.

Nếu client retry:

Request thứ hai lại gọi LLM.

Có thể xảy ra:

Request 1 → LLM
Request 2 → LLM
Request 3 → LLM

→ duplicate inference.

Phải tìm những nguy cơ tương tự.


==================================================
11. ĐÁNH GIÁ THEO AI SYSTEM DESIGN
==================================================

Chấm hệ thống theo 10 tiêu chí:

1. Sync correctness
2. Async correctness
3. Streaming correctness
4. Request classification
5. Latency
6. Scalability
7. Failure isolation
8. Cancellation
9. Retry/idempotency
10. UX

Cho điểm:

0 = chưa có
1 = có nhưng yếu
2 = acceptable
3 = production-grade


==================================================
12. PHÁT HIỆN ANTI-PATTERNS
==================================================

Tìm các anti-pattern:

ANTI-PATTERN 1:
Long-running AI task chạy trong synchronous HTTP request.

ANTI-PATTERN 2:
async def nhưng bên trong toàn blocking code.

ANTI-PATTERN 3:
Chatbot không streaming.

ANTI-PATTERN 4:
Batch job giữ HTTP connection.

ANTI-PATTERN 5:
Client retry làm duplicate LLM inference.

ANTI-PATTERN 6:
Không có job_id cho long-running task.

ANTI-PATTERN 7:
Không có cancellation.

ANTI-PATTERN 8:
Streaming nhưng backend vẫn đợi toàn bộ LLM response.

ANTI-PATTERN 9:
Dùng streaming cho batch processing.

ANTI-PATTERN 10:
Dùng synchronous API cho workload kéo dài hàng phút/hàng giờ.


==================================================
13. ĐẶC BIỆT KIỂM TRA AGENT / LANGGRAPH
==================================================

Nếu hệ thống có Agent/LangGraph:

Kiểm tra:

User
 ↓
Agent
 ↓
Tool
 ↓
RAG
 ↓
LLM
 ↓
Tool
 ↓
LLM
 ↓
Final response

Xác định:

- Agent execution có streaming không?
- Intermediate events có stream không?
- Final answer có stream không?
- Tool execution có block không?
- Long-running agent có thể chạy background không?
- Có thể resume agent không?
- Có thread/job ID không?
- Client disconnect có terminate agent không?

Phân biệt:

Agent conversational → Streaming

Agent long-running → Async

Agent quick response → Sync


==================================================
14. ĐỀ XUẤT ARCHITECTURE SAU KHI AUDIT
==================================================

Sau khi phân tích code hiện tại, đề xuất architecture phù hợp.

Không được đề xuất:

"Mọi thứ chuyển sang async."

Không được đề xuất:

"Mọi thứ chuyển sang streaming."

Thay vào đó phải xây:

                    REQUEST
                       │
                       ▼
               REQUEST ASSESSMENT
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
        FAST          LONG      INTERACTIVE
          │            │            │
          ▼            ▼            ▼
        SYNC          ASYNC     STREAMING
          │            │            │
          ▼            ▼            ▼
       JSON       Job Queue       SSE
                       │
                       ▼
                    Worker
                       │
                       ▼
                      LLM


==================================================
15. OUTPUT FORMAT BẮT BUỘC
==================================================

Trả kết quả theo cấu trúc:

# 1. Executive Summary

Tóm tắt architecture hiện tại trong 10–15 dòng.

# 2. Current Request Flow

Vẽ ASCII diagram.

# 3. Current Delivery Modes

| Request | Mode | Evidence | Problem |

# 4. Sync Audit

Các endpoint sync và đánh giá.

# 5. Async Audit

Các background/queue/job và đánh giá.

# 6. Streaming Audit

SSE/WebSocket/streaming implementation và đánh giá.

# 7. Frontend UX Audit

Phân tích cách frontend nhận response.

# 8. Blocking & Bottleneck Analysis

Liệt kê các điểm blocking.

# 9. Anti-patterns

| Severity | File | Function | Problem | Impact |

Severity:
CRITICAL / HIGH / MEDIUM / LOW

# 10. Request → Delivery Matrix

| Request Type | Current | Recommended | Reason |

# 11. Architecture Score

| Category | Score / 3 | Explanation |

# 12. Recommended Architecture

Vẽ architecture diagram.

# 13. Priority Fixes

P0 = phải sửa
P1 = nên sửa
P2 = cải thiện

# 14. Implementation Plan

Đề xuất từng bước refactor.

QUAN TRỌNG:
Không viết code implementation ở bước audit.
Chỉ đưa code nếu tôi yêu cầu ở bước tiếp theo.

==================================================
FINAL QUESTION
==================================================

Sau khi audit xong, trả lời rõ 5 câu:

1. Hệ thống hiện tại đang dùng Sync, Async hay Streaming?
2. Có request nào đang dùng sai delivery mode không?
3. Có long-running task nào đang block HTTP request không?
4. Chat/Agent hiện tại có cần Streaming không?
5. Nếu production scale lên 10x hoặc 100x, delivery architecture hiện tại
   sẽ gặp vấn đề gì?

Hãy ưu tiên bằng chứng từ source code thay vì suy đoán.