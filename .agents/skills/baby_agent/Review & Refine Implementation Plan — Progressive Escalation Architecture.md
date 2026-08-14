# TASK: Review & Refine Implementation Plan — Progressive Escalation Architecture

Hãy **review và chỉnh sửa Implementation Plan hiện tại** của dự án BabyCare AI theo kiến trúc **Progressive Escalation Architecture (Tier 0 → Tier 1 → Tier 2)**.

**Chưa triển khai code ở bước này. Chỉ cập nhật kế hoạch triển khai.**

Mục tiêu là biến kế hoạch hiện tại thành một specification đủ rõ ràng để sau đó có thể giao cho coding agent triển khai mà không gây chồng chéo trách nhiệm giữa Tier 1, EscalationPolicy và CapabilityRegistry.

---

# 1. KIẾN TRÚC MỤC TIÊU

Thiết kế flow chính:

```text
                         USER QUERY
                              │
                              ▼
                    ┌─────────────────┐
                    │     TIER 0      │
                    │ Deterministic   │
                    │ Fast Path       │
                    └────────┬────────┘
                             │
                       NOT HANDLED
                             │
                             ▼
                    ┌─────────────────┐
                    │     TIER 1      │
                    │ First-line      │
                    │ Solver          │
                    │                 │
                    │ Hybrid RAG      │
                    │ + Reranker      │
                    │ + LLM           │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ Tier1Result     │
                    │ Assessment      │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ Escalation      │
                    │ Policy          │
                    └────────┬────────┘
                             │
                    ┌────────┴────────┐
                    │                 │
                 NO ESCALATE       ESCALATE
                    │                 │
                    ▼                 ▼
                 RESPONSE      Required Capabilities
                                      │
                                      ▼
                              ┌─────────────────┐
                              │ Capability      │
                              │ Registry        │
                              └────────┬────────┘
                                       │
                                       ▼
                              ┌─────────────────┐
                              │     TIER 2      │
                              │ Specialized     │
                              │ Agent           │
                              └─────────────────┘
```

Nguyên tắc:

```text
Tier 0
= Deterministic Solver

Tier 1
= Knowledge-grounded First-line Solver

EscalationPolicy
= Capability Requirement Evaluator

CapabilityRegistry
= Specialist Resolver

Tier 2
= Deep Reasoning / Tool-based Specialist
```

---

# 2. LOẠI BỎ KEYWORD / DOMAIN ROUTING

Trong kế hoạch mới phải ghi rõ:

**KHÔNG được routing Tier 1 → Tier 2 chỉ dựa vào keyword hoặc domain.**

Không được:

```python
if "dinh dưỡng" in query:
    route_to_nutrition_agent()
```

Không được:

```python
if domain == "nutrition":
    escalate()
```

Không được:

```python
if "sốt" in query:
    health_agent()
```

Thay vào đó:

```text
Query
 ↓
Requirement Analysis
 ↓
Reasoning Requirement
Personalization Requirement
Tool Requirement
Cross-domain Requirement
Safety Requirement
Evidence Sufficiency
 ↓
EscalationPolicy
 ↓
Required Capabilities
 ↓
CapabilityRegistry
 ↓
Tier 2 Specialist
```

**Domain chỉ được sử dụng ở bước cuối để tìm Agent có capability phù hợp, không phải là trigger để escalation.**

---

# 3. TIER 0

Giữ Tier 0 là deterministic fast path.

Nhiệm vụ:

```text
"Có xử lý chắc chắn bằng Pure Code / DB được không?"
```

Các request có thể xử lý:

* Greeting
* Latest feeding
* Latest medication
* Today's feeding total
* Current weight
* Current height
* Simple deterministic DB lookup

Flow:

```python
fast_result = tier0.try_extract(query)

if fast_result.handled:
    return fast_result.response
```

Nếu không chắc chắn:

```python
handled = False
```

→ Tier 1.

Tier 0 phải conservative.

Không được dùng keyword đơn lẻ để nuốt các mixed/complex queries.

Ví dụ:

```text
"Bé vừa bú 120ml nhưng sau đó nôn, có sao không?"
```

Không được xử lý như một simple feeding lookup.

→ Tier 1.

---

# 4. TIER 1 — FIRST-LINE SOLVER

Tier 1 là **solver mặc định** cho mọi request mà Tier 0 không xử lý được.

Tier 1 sử dụng:

```text
Query
 ↓
Hybrid Retrieval
(Dense + BM25)
 ↓
Reranker
 ↓
Context
 ↓
LLM
 ↓
Knowledge-grounded Answer
```

Tier 1 có thể xử lý mọi domain nếu câu hỏi có thể trả lời bằng knowledge + reasoning cơ bản.

Ví dụ:

```text
"Trẻ 6 tháng nên ngủ bao nhiêu giờ?"
→ Tier 1

"Bé 7 tháng có thể ăn trứng chưa?"
→ Tier 1

"WHO khuyến nghị trẻ dưới 1 tuổi uống bao nhiêu sữa?"
→ Tier 1
```

Không được chuyển các câu hỏi trên sang Tier 2 chỉ vì chúng thuộc Health/Nutrition/Sleep.

Không ghi mục tiêu là "Tier 1 trả lời 100%".

Thay bằng:

> Tier 1 phải ưu tiên xử lý mọi câu hỏi knowledge-grounded khi evidence đủ và không yêu cầu capability vượt quá Tier 1.

---

# 5. THIẾT KẾ LẠI `Tier1Result`

Không để Tier 1 quyết định routing cuối cùng.

**Loại bỏ:**

```python
should_escalate: bool
```

khỏi `Tier1Result`.

`Tier1Result` chỉ mô tả:

> Tier 1 đã hiểu request cần gì và bản thân Tier 1 có những giới hạn gì.

Thiết kế:

```python
class Tier1Result(BaseModel):

    answer: str

    # Evidence
    evidence_sufficient: bool
    retrieval_confidence: float

    # Reasoning requirement
    requires_deep_reasoning: bool
    requires_multi_document_synthesis: bool
    requires_cross_domain_reasoning: bool

    # Capability requirement
    requires_personal_analysis: bool
    requires_specialized_tools: bool

    # Safety
    safety_sensitive: bool

    # Context reuse
    retrieved_documents: list
    reasoning_context: dict
```

Có thể bổ sung field nếu codebase hiện tại cần, nhưng phải giữ separation of concerns.

---

# 6. TẠO `EscalationDecision`

Tạo schema riêng:

```python
class EscalationDecision(BaseModel):

    should_escalate: bool

    required_capabilities: list[str]

    escalation_reason: str | None
```

Trách nhiệm:

```text
Tier1Result
       ↓
EscalationPolicy
       ↓
EscalationDecision
```

Không để Tier 1 tự quyết định:

```python
should_escalate = True
```

---

# 7. ESCALATION POLICY

Tạo:

```text
app/AI_agents/orchestrator/escalation_policy.py
```

Class:

```python
class EscalationPolicy:

    def evaluate(
        self,
        tier1_result: Tier1Result
    ) -> EscalationDecision:
        ...
```

Policy phải đánh giá các dimension:

```text
Evidence sufficiency
+
Reasoning requirement
+
Personalization requirement
+
Specialized tool requirement
+
Cross-domain reasoning
+
Safety sensitivity
```

Ví dụ:

### Tier 1

```text
Question:
"Bé 7 tháng có thể ăn trứng chưa?"

Evidence = sufficient
Deep reasoning = false
Personal analysis = false
Tools = false

→ should_escalate = false
```

### Tier 2

```text
Question:
"Dựa trên lịch sử 14 ngày ăn uống + cân nặng,
phân tích tại sao bé tăng cân chậm."

Evidence = available
Deep reasoning = true
Personal analysis = true
Tools = true

→ should_escalate = true
```

---

# 8. KHÔNG DÙNG RETRIEVAL SCORE LÀM ROUTER DUY NHẤT

Không triển khai:

```python
if retrieval_score < 0.7:
    escalate()
```

Retrieval confidence chỉ là một feature.

Ví dụ:

```text
High retrieval confidence
+
High personalization requirement
=
Still Tier 2
```

Ngược lại:

```text
Low retrieval confidence
+
Simple question
=
Có thể cần retry/retrieve tốt hơn trước khi escalate
```

Do đó kế hoạch phải phân biệt:

```text
Evidence problem
vs
Reasoning problem
vs
Capability problem
```

---

# 9. CAPABILITY REGISTRY

Sửa:

```text
app/AI_agents/core/capability_registry.py
```

Loại bỏ:

```text
health_keywords
nutrition_keywords
logging_keywords
```

Registry KHÔNG chịu trách nhiệm quyết định escalation.

Nó chỉ làm:

> "Agent nào sở hữu capability mà EscalationPolicy yêu cầu?"

API nên hướng tới:

```python
resolve_agent_by_capability(
    required_capabilities: list[str]
)
```

Không phụ thuộc trực tiếp vào keyword trong query.

Ví dụ:

```json
{
  "required_capabilities": [
    "personal_history_access",
    "growth_analysis",
    "nutrition_analysis"
  ]
}
```

Registry tìm Agent có capabilities phù hợp.

---

# 10. CAPABILITY MODEL

Kế hoạch phải định nghĩa rõ capability của Tier 2 agents.

Ví dụ:

### NutritionAgent

```text
nutrition_analysis
nutrition_history_access
feeding_analysis
growth_nutrition_correlation
```

### HealthAgent

```text
health_analysis
health_history_access
symptom_analysis
medical_record_access
```

### VoiceLoggingAgent

```text
structured_logging
feeding_logging
sleep_logging
diaper_logging
```

Capability là metadata của Agent.

Không phải keyword trigger.

---

# 11. TIER 1 → TIER 2 HANDOFF

Khi escalation:

```text
Tier1Result
 ↓
EscalationDecision
 ↓
CapabilityRegistry
 ↓
Specialist Agent
```

Tạo `HandOffNotice` chứa:

```python
HandOffNotice(
    source_agent="tier1",
    target_agent_id="nutrition_agent",
    reason="personalized_analysis",
    original_query=query,
    context=tier1_result.reasoning_context
)
```

Tier 2 phải nhận:

```text
Original Query
+
Tier 1 Retrieved Documents
+
Tier 1 Reasoning Context
+
Escalation Reason
+
Required Capabilities
```

---

# 12. CONTEXT REUSE

Tier 2 không được mặc định chạy lại toàn bộ:

```text
Dense Retrieval
+
BM25
+
Reranker
```

nếu Tier 1 context đã đủ.

Tier 2 chỉ retrieve thêm khi:

```text
Tier 1 evidence insufficient for specialist task
```

hoặc cần domain-specific documents/tool data.

Flow:

```text
Tier 1 RAG
    │
    ▼
Retrieved Documents
    │
    ├── Enough → Tier 2 reuse
    │
    └── Not enough → Specialist retrieval
```

---

# 13. ORCHESTRATOR

Refactor `run_agent` và `run_agent_stream` thành:

```python
# TIER 0
fast_result = tier0.try_extract(query)

if fast_result.handled:
    return fast_result.response


# TIER 1
tier1_result = tier1.solve(query)


# ESCALATION
decision = escalation_policy.evaluate(
    tier1_result
)

if not decision.should_escalate:
    return tier1_result.answer


# CAPABILITY RESOLUTION
agent = capability_registry.resolve_agent_by_capability(
    decision.required_capabilities
)


# TIER 2
return agent.execute(
    query=query,
    tier1_context=tier1_result.reasoning_context,
    retrieved_documents=tier1_result.retrieved_documents
)
```

Streaming phải giữ nguyên SSE contract hiện tại:

```text
step
tool_step
token
```

Không để việc refactor routing phá vỡ streaming.

---

# 14. TIER 2

Tier 2 là:

> Specialized Deep Reasoning / Tool-based Execution Layer.

Tier 2 được kích hoạt khi request cần:

* Deep reasoning
* Personal history analysis
* Specialized DB tools
* Cross-domain synthesis
* Safety-sensitive personalized analysis

Ví dụ:

```text
"Bé 7 tháng ăn ít hơn 30% trong 14 ngày,
ngủ kém và cân nặng không tăng.
Phân tích nguyên nhân."
```

Tier 2 có thể:

```text
Baby Profile
+
Feeding History
+
Sleep History
+
Growth History
+
Domain RAG
+
Tools
+
Deep Reasoning
```

---

# 15. LOOP SAFEGUARDS

Giữ:

```python
max_handoffs = 3
visited_agents = set()
execution_timeout = 90.0
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

Ưu tiên flow:

```text
T0 → T1 → T2
```

Không biến thành:

```text
T0 → T1 → T2 → T1 → T2
```

---

# 16. TEST PLAN

Cập nhật test theo **reasoning/capability requirement**, không chỉ expected agent.

### T0

```text
"Xin chào"
"Cữ bú gần nhất?"
"Tổng sữa hôm nay?"
```

Expected:

```text
Tier 0 handled = true
LLM calls = 0
```

---

### T1

```text
"Trẻ 6 tháng nên ngủ bao nhiêu giờ?"
"Bé 7 tháng có thể ăn trứng chưa?"
"WHO khuyến nghị trẻ dưới 1 tuổi uống bao nhiêu sữa?"
```

Expected:

```text
Tier 0 = false
Tier 1 = executed
evidence_sufficient = true
requires_personal_analysis = false
requires_specialized_tools = false
should_escalate = false
```

---

### T2

```text
"Dựa trên lịch sử 14 ngày,
phân tích tại sao bé tăng cân chậm."
```

Expected:

```text
Tier 1 = executed

requires_personal_analysis = true
requires_specialized_tools = true

EscalationPolicy:
should_escalate = true

required_capabilities:
[
    "personal_history_access",
    "growth_analysis",
    "nutrition_analysis"
]

CapabilityRegistry:
→ NutritionAgent
```

---

### Cross-domain

```text
"Bé ăn ít, ngủ kém, cân nặng không tăng.
Hãy phân tích mối liên hệ."
```

Expected:

```text
requires_cross_domain_reasoning = true
requires_personal_analysis = true
should_escalate = true
```

---

### False Positive

```text
"Tôi đang đọc bài viết về dinh dưỡng thể thao."
```

Expected:

```text
Không route NutritionAgent chỉ vì keyword "dinh dưỡng".
```

---

### Mixed Query

```text
"Bé vừa bú 120ml nhưng sau đó nôn, có sao không?"
```

Expected:

```text
Tier 0 = not handled

Tier 1 = executed

Không được coi đây là deterministic feeding lookup.

Nếu assessment xác định:
safety_sensitive = true
personal_analysis = true

→ Escalate Tier 2.
```

---

# 17. OBSERVABILITY

Log mỗi request:

```json
{
  "tier0_handled": false,
  "tier1_executed": true,

  "evidence_sufficient": true,
  "retrieval_confidence": 0.91,

  "requires_deep_reasoning": true,
  "requires_personal_analysis": true,
  "requires_specialized_tools": true,
  "requires_cross_domain_reasoning": false,
  "safety_sensitive": false,

  "should_escalate": true,
  "escalation_reason": "personalized_analysis",

  "required_capabilities": [
    "personal_history_access",
    "growth_analysis",
    "nutrition_analysis"
  ],

  "resolved_agent": "nutrition_agent",

  "handoff_count": 1,
  "latency_ms": 1850
}
```

Mục tiêu quan sát:

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

---

# 18. DELIVERABLE CỦA IMPLEMENTATION PLAN

Sau khi chỉnh sửa, trả về một Implementation Plan hoàn chỉnh gồm:

1. Architecture Overview
2. Responsibility Boundaries
3. Data Contracts
4. Tier 0 changes
5. Tier 1 changes
6. Tier1Result
7. EscalationDecision
8. EscalationPolicy
9. CapabilityRegistry
10. Tier 1 → Tier 2 HandOff
11. Context Reuse
12. Tier 2 changes
13. Orchestrator changes
14. Streaming compatibility
15. Loop safeguards
16. Test plan
17. Observability
18. Migration strategy
19. Risks / edge cases
20. Files to modify/create

---

# 19. QUY TẮC QUAN TRỌNG NHẤT

Trong toàn bộ kế hoạch mới, phải giữ đúng các nguyên tắc:

```text
❌ Keyword → Tier 2
❌ Domain → Tier 2
❌ Retrieval score thấp → Tier 2 ngay lập tức
❌ Tier 1 tự quyết định routing cuối cùng
❌ CapabilityRegistry tự quyết định escalation

✅ Tier 0 → deterministic capability
✅ Tier 1 → knowledge-grounded first-line solving
✅ Tier1Result → capability/reasoning assessment
✅ EscalationPolicy → escalation decision
✅ CapabilityRegistry → specialist resolution
✅ Tier 2 → deep reasoning + tools + personalization
```

Core principle:

> **Không hỏi "Query này thuộc domain nào?" để quyết định Tier 2.**
>
> **Hãy hỏi "Request này cần những capability/reasoning nào mà Tier 1 không có?"**

Chỉ sau khi xác định được capability requirement mới chọn Specialist Agent.

---

## OUTPUT FORMAT

Không viết code implementation.

Hãy trả về **Implementation Plan đã được chỉnh sửa hoàn chỉnh**, chỉ rõ:

* Những phần nào của plan cũ được giữ lại.
* Những phần nào cần thay đổi.
* Những field/API nào được thay đổi.
* Responsibility của từng component.
* Data flow giữa Tier 0 → Tier 1 → EscalationPolicy → CapabilityRegistry → Tier 2.
* Các test case cần bổ sung.
* Những rủi ro khi migrate từ architecture hiện tại.

Không được quay lại thiết kế keyword/domain routing dưới bất kỳ hình thức nào.
