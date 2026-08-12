# TASK: Refactor BabyCare AI thành Progressive Escalation Architecture — Tier 0 → Tier 1 → Tier 2

Bạn đang làm việc trên codebase **BabyCare AI**.

## Mục tiêu

Refactor cơ chế routing hiện tại thành kiến trúc:

```text
User Query
    │
    ▼
TIER 0 — Deterministic Fast Path
    │
    ├── Có thể xử lý chắc chắn → Response
    │
    └── Không chắc / Complex → TIER 1
                              │
                              ▼
                       TIER 1 — First-line Solver
                       Hybrid RAG + LLM
                              │
                    Can Tier 1 answer well?
                         /            \
                       YES             NO
                        │               │
                        ▼               ▼
                    Response         TIER 2
                                Escalation Path
                                      │
                                      ▼
                              Specialized Agent
```

### Nguyên tắc kiến trúc bắt buộc

**Không routing Tier 1 → Tier 2 chỉ bằng keyword/domain.**

Không được triển khai kiểu:

```python
if "dinh dưỡng" in query:
    return nutrition_agent
```

hoặc:

```python
if domain == "nutrition":
    route_to_tier2()
```

Vì Tier 1 đã có Hybrid RAG và hoàn toàn có thể trả lời các câu hỏi Health/Nutrition/Sleep đơn giản.

Routing phải dựa trên:

> **Reasoning Requirement + Answerability**

Domain chỉ được sử dụng **sau khi quyết định rằng Tier 2 thực sự cần thiết**, để chọn specialist agent phù hợp.

---

# 1. TIER 0 — Deterministic Fast Path

Giữ lại cơ chế Fast Path hiện tại.

Tier 0 xử lý các request có thể xác định hoàn toàn bằng code:

* Greeting
* Deterministic DB lookup
* Simple tracking lookup
* Latest feeding
* Latest medication
* Today's total feeding
* Height / weight lookup
* Các request tương tự đã có deterministic handler

Ví dụ:

```text
"Bé uống bao nhiêu ml hôm nay?"
→ Firestore → Response

"Cữ bú gần nhất?"
→ Firestore → Response

"Xin chào"
→ Fast greeting → Response
```

### Quy tắc

Tier 0 phải **conservative**.

Nếu parser không chắc chắn:

```python
try_handle(query) -> None
```

thì chuyển sang Tier 1.

Không được để keyword đơn lẻ khiến Tier 0 xử lý sai.

Ví dụ:

```text
"Bé vừa bú 120ml nhưng sau đó nôn, có sao không?"
```

Không được coi đây là DB lookup chỉ vì có từ `"bú"`.

→ Tier 1.

---

# 2. TIER 1 — First-line Solver

Tier 1 là **solver mặc định cho mọi request không xử lý được ở Tier 0**.

Tier 1 phải sử dụng pipeline Hybrid RAG hiện tại:

```text
Query
 ↓
Query Understanding
 ↓
Dense Retrieval
 +
BM25
 ↓
Reranker
 ↓
Top-K Context
 ↓
LLM
 ↓
Answer
```

Tier 1 có thể xử lý tất cả các domain nếu evidence đủ:

* Nutrition
* Health
* Sleep
* Growth
* Development
* General childcare

Không được tự động chuyển sang Tier 2 chỉ vì query thuộc một domain chuyên môn.

### Ví dụ phải ở Tier 1

```text
"Trẻ 6 tháng nên ngủ bao nhiêu giờ?"
```

```text
"Bé 7 tháng có thể bắt đầu ăn trứng chưa?"
```

```text
"WHO khuyến nghị trẻ dưới 1 tuổi uống bao nhiêu sữa?"
```

Nếu Hybrid RAG tìm được evidence tốt và câu hỏi không yêu cầu personalized reasoning:

→ Tier 1 trả lời.

---

# 3. TIER 1 PHẢI CÓ ANSWERABILITY / ESCALATION EVALUATION

Sau khi Tier 1 retrieval + reasoning, không trả trực tiếp string.

Tạo một structured result:

```python
class Tier1Result:
    answer: str

    # Retrieval / evidence
    evidence_sufficient: bool
    retrieval_confidence: float

    # Reasoning requirements
    requires_deep_reasoning: bool
    requires_multi_document_synthesis: bool
    requires_cross_domain_reasoning: bool

    # Personalization / tools
    requires_personal_analysis: bool
    requires_specialized_tools: bool

    # Safety
    safety_sensitive: bool

    # Routing
    should_escalate: bool
    escalation_reason: str | None

    # Reusable context for Tier 2
    retrieved_documents: list
    reasoning_context: dict
```

Không để LLM trực tiếp quyết định:

```json
{
  "route": "nutrition_agent"
}
```

Thay vào đó LLM/classifier chỉ đánh giá capability requirement:

```json
{
  "evidence_sufficient": false,
  "requires_deep_reasoning": true,
  "requires_personal_analysis": true,
  "requires_specialized_tools": true
}
```

Sau đó **Python/Orchestrator quyết định escalation**.

---

# 4. ESCALATION POLICY

Tạo một module riêng:

```text
app/AI_agents/orchestrator/escalation_policy.py
```

Ví dụ:

```python
class EscalationPolicy:

    def should_escalate(self, result: Tier1Result) -> bool:
        ...
```

Tier 2 nên được kích hoạt khi Tier 1 phát hiện một hoặc nhiều điều kiện quan trọng:

### A. Deep reasoning

```text
"phân tích nguyên nhân..."
"đánh giá tình trạng..."
"so sánh nhiều yếu tố..."
"dựa trên lịch sử..."
```

Không match keyword trực tiếp để route, mà keyword chỉ có thể là feature.

### B. Personalized analysis

Ví dụ:

```text
"Dựa trên lịch sử ăn uống 14 ngày của bé..."
"Dựa trên cân nặng của bé..."
```

→ cần dữ liệu cá nhân → có khả năng escalate.

### C. Multi-document synthesis

Cần tổng hợp nhiều nguồn tài liệu thay vì trả lời từ một evidence đơn.

### D. Cross-domain reasoning

Ví dụ:

```text
Feeding
+
Sleep
+
Growth
+
Symptoms
```

→ Tier 2.

### E. Specialized tools

Nếu cần:

```text
Firestore history
Growth calculation
Medical tool
Nutrition calculation
```

→ Tier 2.

### F. Safety-sensitive personalized request

Các yêu cầu y tế cá nhân cần đánh giá sâu hơn nên có thể escalate.

---

# 5. KHÔNG dùng một retrieval score duy nhất

Không triển khai:

```python
if retrieval_score < 0.7:
    tier2()
```

Retrieval score chỉ là **một feature**.

Ví dụ:

```text
retrieval_confidence
+
reasoning_requirement
+
personalization_requirement
+
tool_requirement
+
multi_domain_requirement
+
safety_requirement
```

mới quyết định escalation.

---

# 6. TIER 1 → TIER 2

Khi escalation xảy ra, sử dụng explicit `HandOffNotice`.

Ví dụ:

```python
HandOffNotice(
    source_agent="tier1",
    target_agent="nutrition_agent",
    reason="personalized_analysis",
    original_query=query,
    context=tier1_context
)
```

Tuy nhiên:

**Tier 1 không được quyết định specialist bằng keyword.**

Quy trình phải là:

```text
Tier 1
 ↓
Determine escalation required
 ↓
Capability Registry
 ↓
Find capable Tier 2 agent
 ↓
HandOffNotice
 ↓
Orchestrator
 ↓
Tier 2
```

Ví dụ:

```text
Complex nutrition reasoning
→ NutritionAgent

Complex medical reasoning
→ HealthAgent

Complex voice logging
→ VoiceLoggingAgent

Out of scope
→ OutOfScopeAgent
```

---

# 7. REUSE CONTEXT — KHÔNG RETRIEVE LẠI VÔ ÍCH

Tier 2 phải nhận context mà Tier 1 đã tạo:

```text
Original Query
+
Baby Context
+
Retrieved Documents
+
Reranker Results
+
Tier 1 Reasoning
+
Escalation Reason
```

Ví dụ:

```python
Tier2Request(
    original_query=query,
    tier1_context=result.reasoning_context,
    retrieved_documents=result.retrieved_documents,
    escalation_reason=result.escalation_reason
)
```

Tier 2 chỉ thực hiện thêm:

```text
Specialized DB access
+
Domain-specific RAG
+
Specialized tools
+
Deep reasoning
```

Không được làm lại toàn bộ Tier 1 pipeline nếu không cần thiết.

---

# 8. TIER 2 — ESCALATION PATH

Tier 2 không phải "nơi chứa tất cả câu hỏi chuyên ngành".

Tier 2 chỉ xử lý:

> Requests mà Tier 1 không thể giải quyết đáng tin cậy bằng knowledge-grounded answering.

Tier 2 có:

```text
Specialized Agent
 ↓
Personal Data
 ↓
Domain RAG
 ↓
Tools
 ↓
Multi-step Reasoning
 ↓
Final Answer
```

Ví dụ:

```text
"Phân tích tại sao bé tăng cân chậm dựa trên lịch sử ăn uống,
cân nặng và giấc ngủ trong 14 ngày."
```

→ Tier 2.

---

# 9. KHÔNG CẦN TIER 2 → TIER 1 TRONG FLOW THÔNG THƯỜNG

Ưu tiên kiến trúc:

```text
T0 → T1 → T2
```

thay vì:

```text
T0 → T1 → T2 → T1 → T2
```

Nếu Tier 2 phát hiện request không thuộc capability của nó:

```text
Tier 2
 ↓
Capability mismatch
 ↓
Orchestrator
 ↓
Another Tier 2 Agent
```

Chỉ fallback về Tier 1 nếu thật sự cần.

---

# 10. LOOP SAFEGUARDS

Giữ và nâng cấp các safeguard hiện tại:

```python
max_handoffs = 3
visited_agents = set()
execution_timeout = 90.0
```

Bổ sung nếu phù hợp:

```python
max_tool_calls
max_total_tokens
max_execution_steps
```

Không cho phép:

```text
Agent A
 ↓
Agent B
 ↓
Agent A
```

lặp vô hạn.

---

# 11. ORCHESTRATOR FLOW

Refactor `AgentOrchestrator` thành flow rõ ràng:

```python
def process(query):

    # -------------------------
    # TIER 0
    # -------------------------
    fast_result = tier0.try_handle(query)

    if fast_result.handled:
        return fast_result.response

    # -------------------------
    # TIER 1
    # -------------------------
    tier1_result = tier1.solve(query)

    # -------------------------
    # ESCALATION
    # -------------------------
    if not escalation_policy.should_escalate(tier1_result):
        return tier1_result.answer

    # -------------------------
    # TIER 2
    # -------------------------
    tier2_agent = capability_registry.resolve(
        query=query,
        tier1_result=tier1_result
    )

    return tier2_agent.execute(
        query=query,
        context=tier1_result.reasoning_context
    )
```

Mục tiêu là flow phải dễ đọc:

```text
T0 → T1 → Evaluate → T2 if needed
```

---

# 12. Test cases bắt buộc

Sau khi refactor phải tạo test cho ít nhất các nhóm sau.

### Tier 0

```text
"Xin chào"
"Cữ bú gần nhất?"
"Tổng sữa hôm nay?"
```

→ T0.

### Tier 1

```text
"Trẻ 6 tháng ngủ bao nhiêu giờ?"
"Bé 7 tháng có thể ăn trứng chưa?"
"WHO khuyến nghị..."
```

→ T1.

### Tier 2

```text
"Dựa trên lịch sử 14 ngày, phân tích tại sao bé tăng cân chậm."
"Bé ăn ít + ngủ kém + cân nặng không tăng, phân tích nguyên nhân."
```

→ T2.

### False Positive

```text
"Tôi đang đọc bài viết về dinh dưỡng thể thao."
```

Không được tự động:

```text
→ NutritionAgent
```

### Mixed Query

```text
"Bé vừa bú 120ml nhưng sau đó nôn, có sao không?"
```

Không được T0 lookup.

→ T1 hoặc T2 tùy escalation evaluation.

---

# 13. Logging / Observability

Mỗi request phải log:

```json
{
  "query": "...",
  "tier0_handled": false,
  "tier1_executed": true,
  "retrieval_confidence": 0.84,
  "requires_deep_reasoning": true,
  "requires_personal_analysis": true,
  "should_escalate": true,
  "escalation_reason": "personalized_analysis",
  "tier2_agent": "nutrition_agent",
  "handoff_count": 1,
  "latency_ms": 1840
}
```

Mục đích là sau này có thể đánh giá:

* Tier 0 hit rate
* Tier 1 answer rate
* Tier 2 escalation rate
* False escalation
* Missed escalation
* Average latency
* Token usage
* Cost/request

---

# 14. KPI quan trọng

Sau khi triển khai, đo:

```text
Tier 0 Hit Rate
Tier 1 Resolution Rate
Tier 2 Escalation Rate
False Escalation Rate
Missed Escalation Rate
Average Latency
LLM Tokens / Request
Cost / Request
```

Mục tiêu kiến trúc:

```text
                    100% Requests
                         │
              ┌──────────┼──────────┐
              ▼          ▼          ▼
             T0         T1         T2
          cheapest    default    expensive
```

Tối ưu không phải là:

> "Đưa càng nhiều request vào Tier 1 càng tốt."

Mà là:

> **Tier thấp nhất có đủ năng lực xử lý request thì dừng ở tier đó.**

---

# Deliverables

Hãy thực hiện theo thứ tự:

1. **Inspect toàn bộ implementation hiện tại** của:

   * `agent_orchestrator.py`
   * `fast_extractor.py`
   * `chat_graph.py`
   * `capability_registry.py`
   * `task_planner.py`
   * các Tier 2 workflow
   * RAG/retriever/reranker pipeline.

2. **Không rewrite toàn bộ hệ thống.**
   Reuse implementation hiện tại tối đa.

3. Refactor thành:

```text
Tier 0
   ↓
Tier 1 First-line Solver
   ↓
Escalation Evaluator
   ↓
Tier 2
```

4. Loại bỏ routing Tier 1 → Tier 2 dựa đơn thuần trên keyword/domain.

5. Giữ `CapabilityRegistry` nhưng chuyển responsibility của nó thành:

   * capability discovery
   * specialist resolution
   * không tự quyết định escalation chỉ bằng keyword.

6. Tạo `Tier1Result`.

7. Tạo `EscalationPolicy`.

8. Tạo explicit `HandOffNotice`.

9. Reuse Tier 1 context khi escalate.

10. Thêm unit/integration tests cho toàn bộ routing scenarios.

11. Không làm thay đổi behavior của các deterministic Tier 0 handlers nếu không cần thiết.

12. Sau khi hoàn thành, báo cáo:

* Files đã thay đổi
* Architecture trước/sau
* Logic escalation mới
* Các keyword routing đã được loại bỏ/thay thế ở đâu
* Test results
* Các vấn đề còn tồn tại
* Đề xuất threshold/heuristic cần benchmark thêm.

## Architectural principle cuối cùng

```text
TIER 0
"Can I answer this deterministically?"
        │
        └── NO
             ↓
TIER 1
"Can I answer this reliably using knowledge + Hybrid RAG?"
        │
        └── NO / insufficient
             ↓
TIER 2
"Does this require deep reasoning, personalization,
specialized tools, or cross-domain synthesis?"
```

**Không route theo keyword.
Không route theo domain đơn thuần.
Route theo capability và reasoning requirement.**

Ưu tiên **cheap → reliable → deep**, và chỉ escalate khi thực sự cần.
