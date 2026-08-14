Bạn là Senior Staff Engineer chuyên về Production AI Infrastructure, Distributed Systems, LLM Serving, Observability và Reliability.

Hãy AUDIT TOÀN BỘ CODEBASE hiện tại dựa trên specification sau:

============================================================
REFERENCE ARCHITECTURE
============================================================

Core principle:

    Optimize the hot path.
    Decouple everything else.

Primary path:

    Request → tokens

Return transport:

    Streaming HTTP / SSE

State systems:

    Cache + Database

Compute boundary:

    Model Router + GPU / LLM Provider

Background work:

    Event Bus + Async Workers

North-star metric:

    Useful First Token

============================================================
1. REQUEST LIFECYCLE
============================================================

Kiểm tra toàn bộ lifecycle:

1. Client creates request envelope
2. Edge / API entry
3. Authentication + admission
4. Chat Orchestrator creates run
5. Hot context from cache
6. Durable conversation history
7. Prompt construction
8. Synchronous guardrails
9. Model Router
10. Inference admission
11. Model inference
12. Token streaming
13. Client incremental rendering
14. Persistence + telemetry

Không được chỉ kiểm tra xem "có class/file tương ứng hay không".

Phải kiểm tra:

- Ai sở hữu responsibility?
- Có dependency nào không cần thiết trên hot path?
- Có synchronous operation nào đang block first token?
- Có retry không kiểm soát?
- Có timeout không?
- Có cancellation propagation không?
- Có fallback không?
- Có tracing xuyên suốt không?
- Có failure policy không?

============================================================
2. SERVICE OWNERSHIP
============================================================

Audit các boundary:

01 Member Client
02 Edge / CDN
03 API Gateway
04 Chat Orchestrator
05 Hot Cache
06 Conversation Database
07 Model Router
08 GPU / Inference Provider
09 Event Bus
10 Async Workers

Với mỗi responsibility, xác định:

- Component hiện tại nào đang thực hiện?
- Có đúng ownership không?
- Có responsibility leakage không?
- Có coupling không cần thiết không?
- Có synchronous dependency nào đáng lẽ phải async?
- Có state nào đang bị đặt sai layer?

Xuất bảng:

| Responsibility | Current Component | Expected Owner | Status | Evidence | Risk |

============================================================
3. MESSAGE VS RUN
============================================================

Kiểm tra hệ thống có phân biệt rõ:

Conversation
Message
Run
Run Event
Usage Ledger

Hay đang coi một request = một message = một run.

Kiểm tra:

- message_id
- conversation_id
- run_id
- request_id
- idempotency_key
- sequence
- finish_reason
- run status
- retry
- fallback
- interrupted stream
- cancellation

Đặc biệt kiểm tra:

"Same authenticated member + conversation + idempotency key
must resolve to the same accepted operation."

Phải phát hiện khả năng duplicate billable generation.

============================================================
4. OBSERVABILITY / TRACE CONTEXT
============================================================

Audit xem có trace context xuyên suốt:

HTTP
 ↓
Middleware
 ↓
Router
 ↓
Orchestrator
 ↓
RAG
 ↓
Reasoner / LLM
 ↓
Model Provider
 ↓
SSE
 ↓
Persistence

Tối thiểu cần kiểm tra:

- trace_id
- request_id
- conversation_id
- run_id
- thread_id
- tenant/member pseudonym
- region
- model
- model routing decision
- prompt_version
- retrieval_version
- policy_version

Tìm chính xác nơi context bị mất.

Không được chỉ nói "thiếu tracing".

Phải chỉ ra:

FILE
CLASS
FUNCTION
LINE
CURRENT BEHAVIOR
MISSING FIELD
IMPACT
RECOMMENDED FIX

============================================================
5. LATENCY WATERFALL
============================================================

Phải kiểm tra từng stage:

request_received
auth
admission
conversation_cache
conversation_db
prompt_construction
guardrail
query_analysis
retrieval
reranking
tool_execution
tier1_solver
escalation
tier2_agent
model_routing
inference_queue
LLM_call
first_token
streaming
persistence

Mỗi stage cần xác định:

- start timestamp
- end timestamp
- duration
- timeout
- error
- trace/run correlation

Đặc biệt:

TTFT:

    first_token_timestamp - request/admission timestamp

Inter-token latency:

    token[n]_timestamp - token[n-1]_timestamp

Decode throughput:

    generated_tokens / decode_duration

Không được dùng:

    total_request_time

thay cho TTFT.

============================================================
6. LLM INFERENCE OBSERVABILITY
============================================================

Kiểm tra:

- model
- provider
- routing decision
- queue time
- time to first token
- prefill time nếu provider expose
- decode duration
- output tokens
- tokens/sec
- input tokens
- cached tokens
- output tokens
- total tokens
- estimated cost
- actual provider cost nếu có
- cancellation
- wasted tokens
- wasted cost
- retry
- fallback

Phải phân biệt:

Application TTFT

vs

Provider/model inference TTFT

Nếu codebase không thể đo provider-level metric, phải ghi rõ:

"NOT OBSERVABLE FROM CURRENT APPLICATION BOUNDARY"

Không được tự suy đoán.

============================================================
7. CACHE / DATABASE
============================================================

Audit:

CACHE

- hit
- miss
- hit ratio
- latency
- stale data
- TTL
- stampede protection
- fallback to DB

DATABASE

- read latency
- write latency
- timeout
- retry
- connection pressure
- pagination
- authorization
- ordered message access

Kiểm tra cache có phải source of truth hay không.

Expected:

Cache = reconstructible acceleration layer

Database = durable source of truth

============================================================
8. RAG OBSERVABILITY
============================================================

Audit:

Query Analyzer
Retriever
BM25
Vector Search
Hybrid Search
Reranker
Context Builder

Đo:

- query analysis latency
- retrieval latency
- reranking latency
- number retrieved
- number reranked
- final context size
- context tokens
- retrieval hit/miss
- retrieval version
- index version

Không được chỉ kiểm tra "có RAG".

Phải xác định chính xác latency contribution của RAG vào TTFT.

============================================================
9. SAFETY
============================================================

Phân biệt rõ:

SYNCHRONOUS SAFETY

và

ASYNC SAFETY

Synchronous:

- authentication
- authorization
- document permission
- output policy
- tool permission
- argument validation
- spending limits
- confirmation gates
- required PII / secret controls

Async:

- deep classifiers
- quality evaluation
- hallucination evaluation
- red-team replay
- abuse analysis
- analytics
- dataset generation

Kiểm tra xem async safety có đang được dùng để thực hiện một control
đáng lẽ phải block trước response hay không.

============================================================
10. STREAMING
============================================================

Audit SSE / Streaming HTTP.

Kiểm tra:

- first token
- token ordering
- sequence number
- duplicate token protection
- terminal event
- completed
- failed
- interrupted
- disconnect
- reconnect
- cancellation
- partial response persistence

Đặc biệt kiểm tra:

Client disconnect
      ↓
API
      ↓
Orchestrator
      ↓
LLM Provider
      ↓
Inference Scheduler

Cancellation có propagate toàn bộ chain hay không?

Nếu không:

đánh dấu là resource leak / wasted generation.

============================================================
11. FAILURE DESIGN
============================================================

Audit các failure scenario:

1. Cache unavailable
2. DB slow
3. DB unavailable
4. RAG unavailable
5. Preferred model saturated
6. Model provider unavailable
7. GPU failure
8. LLM timeout
9. Client disconnect
10. Event bus unavailable
11. Worker lag
12. Redis unavailable
13. Firestore unavailable
14. SSE connection failure

Với mỗi failure:

| Failure | Current Behavior | Expected Degradation | Timeout | Retry | Fallback | Risk |

Không được đề xuất "retry everything".

Retry phải có:

- bounded retry
- exponential backoff
- deadline
- idempotency
- retry budget

============================================================
12. BACKPRESSURE
============================================================

Audit từng queue/boundary:

Client
API
Orchestrator
RAG
LLM
Provider
Event Bus
Workers

Mỗi queue phải có:

- bounded capacity
- timeout
- rejection policy
- overload behavior

Expected overload behavior:

REJECT
SHED
DOWNGRADE
DEFER

Không được:

WAIT INDEFINITELY

Đặc biệt kiểm tra inference admission.

============================================================
13. COST OBSERVABILITY
============================================================

Kiểm tra khả năng tính:

cost per request
cost per run
cost per conversation
cost per successful task
cost per model
cost per tenant
wasted token cost
wasted generation cost

Tất cả LLM calls thuộc một run phải liên kết bằng:

trace_id / run_id

Ví dụ:

QueryAnalyzer
     ↓
RAG
     ↓
Tier1 LLM
     ↓
Escalation
     ↓
Tier2 LLM
     ↓
Tool

Phải tính được:

total_task_cost

Nếu hiện tại không thể:

giải thích chính xác tại sao.

============================================================
14. PRODUCT / QUALITY METRICS
============================================================

Kiểm tra:

- task success
- regeneration
- correction
- abandonment
- negative feedback
- retry
- fallback
- safety block
- policy override
- citation validity
- groundedness
- tool correctness

Phải phân biệt:

Infrastructure metric
vs
Product metric
vs
Quality metric

============================================================
15. PII / LOGGING SECURITY
============================================================

Audit TOÀN BỘ:

logger.info
logger.warning
logger.error
logger.debug
print()
JSONL
structured logs
exception messages
tracing attributes
SSE logs
LLM logs

Tìm:

- raw prompt
- system prompt
- baby name
- DOB
- medical information
- allergies
- medication
- parent information
- access tokens
- API keys
- authorization headers
- conversation content

Đặc biệt:

Không được đưa raw prompt vào trace/log chỉ để debug.

Thay bằng:

prompt_hash
prompt_length
token_count
anonymized metadata
reference ID

============================================================
16. VERSIONING
============================================================

Kiểm tra có tracking:

prompt_version
model_version
retrieval_version
index_version
policy_version
tool_version
schema_version

Nếu prompt nằm trong .txt/.py static:

phải đánh giá khả năng reproducibility.

Mục tiêu:

Biết chính xác:

"Response này được tạo bằng model + prompt + retrieval + policy nào?"

============================================================
17. ASYNC DECOUPLING
============================================================

Tìm mọi operation đang nằm trên hot path nhưng không cần thiết để tạo first token.

Candidate:

- analytics
- billing aggregation
- telemetry
- deep evaluation
- feedback processing
- quality scoring
- audit processing
- long-term persistence nếu product semantics cho phép

Phân loại:

MUST BLOCK FIRST TOKEN

vs

CAN BE ASYNC

Không được tự động async hóa persistence nếu product cần durable acknowledgement.

============================================================
18. HOT PATH ANALYSIS
============================================================

Xác định chính xác:

REQUEST
 ↓
[HOT PATH]
 ↓
FIRST TOKEN

Xuất:

HOT PATH:

1.
2.
3.
4.
...

BLOCKING DEPENDENCIES:

1.
2.
3.
...

UNNECESSARY BLOCKING:

1.
2.
3.
...

ASYNC CANDIDATES:

1.
2.
3.
...

============================================================
19. REQUIRED FINAL OUTPUT
============================================================

Không chỉ đưa nhận xét chung.

Xuất báo cáo theo format:

# PRODUCTION AI ARCHITECTURE AUDIT

## A. Executive Summary

- Architecture score /100
- Reliability score /100
- Observability score /100
- Latency readiness score /100
- Cost observability score /100
- Security/logging score /100

## B. Current Architecture

Vẽ ASCII architecture thực tế của CODEBASE.

## C. Actual Hot Path

Vẽ:

Request
 ↓
...
 ↓
First Token

## D. Latency Waterfall

| Stage | File | Function | Current latency metric | Blocking? | Risk |

## E. Trace Propagation

| Boundary | trace_id | request_id | run_id | Status |

## F. Observability Gap Matrix

| Requirement | Current | Evidence | Severity | Fix |

Severity:

P0 = security/data loss/correctness/major production risk
P1 = major latency/reliability/operability issue
P2 = important improvement
P3 = optimization

## G. PII / Security Audit

Liệt kê từng vị trí có nguy cơ leak.

## H. Cost Audit

Cho biết có thể tính:

cost/request
cost/run
cost/task
wasted cost

hay không.

## I. Failure Matrix

| Failure | Current | Expected | Status |

## J. Hot Path Optimization

Chỉ ra từng dependency có thể loại khỏi blocking path.

## K. Top 10 Production Risks

Sắp xếp theo P0 → P3.

## L. Implementation Plan

Chia:

PHASE 0 — Security / P0
PHASE 1 — Trace Context
PHASE 2 — Latency Metrics
PHASE 3 — Cost & Usage
PHASE 4 — Failure / Backpressure
PHASE 5 — Async Decoupling
PHASE 6 — Dashboard / SLO

Mỗi task phải có:

- file
- class/function
- exact change
- new field/metric
- dependency
- risk
- acceptance criteria

============================================================
20. CRITICAL AUDIT RULES
============================================================

RULE 1:
Không được đánh giá dựa trên filename בלבד.
Phải đọc implementation.

RULE 2:
Không được nói "có observability" chỉ vì có logger.

Logger != Metric
Logger != Trace
Logger != SLO

RULE 3:
Không được nói "có streaming" chỉ vì function có yield.

Phải kiểm tra thực tế first token, cancellation, sequence và terminal event.

RULE 4:
Không được nói "có cost tracking" chỉ vì có estimated_cost_usd.

Phải kiểm tra aggregation theo run/task.

RULE 5:
Không được nói "có RAG" chỉ vì có retriever.

Phải đo latency contribution.

RULE 6:
Không được giả định provider expose queue/prefill/decode metrics.

Nếu application không có quyền truy cập:
ghi rõ NOT OBSERVABLE.

RULE 7:
Không được tự tạo bằng chứng.

Mọi finding phải có:

FILE
FUNCTION/CLASS
LINE nếu xác định được
CODE BEHAVIOR
IMPACT

RULE 8:
Nếu chưa đọc đủ code để kết luận:
ghi:

"INSUFFICIENT EVIDENCE"

và liệt kê file/function cần inspect tiếp.

RULE 9:
Không sửa code ngay.

Đầu tiên chỉ AUDIT.

RULE 10:
Sau audit phải đưa ra:
P0 / P1 / P2 / P3

và acceptance criteria có thể test được.

============================================================
FINAL QUESTION
============================================================

Sau khi audit toàn bộ codebase, hãy trả lời chính xác:

"Liệu hệ thống hiện tại đã thực sự đạt kiến trúc:

    Request → Useful First Token

với:

    bounded hot path
    distributed trace
    measurable TTFT
    latency waterfall
    cancellation propagation
    bounded inference admission
    cost-per-task
    PII-safe logging
    async side paths
    explicit failure policies

hay chưa?"

Nếu CHƯA:

Không chỉ nói "chưa".

Hãy chỉ ra chính xác 5–10 thay đổi cần thực hiện để đạt kiến trúc đó,
xếp theo P0/P1/P2/P3 và kèm acceptance criteria.