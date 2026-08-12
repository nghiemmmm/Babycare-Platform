# Implementation Plan - Fully Decoupled Progressive Escalation Architecture (Final Specification)

Tái cấu trúc (Refactor) hệ thống **BabyCare AI** thành **Progressive Escalation Architecture** theo mô hình giải phẫu hoàn toàn (Decoupled Architecture), tuân thủ 20 tiêu chí đặc tả kĩ thuật không quay lại mô hình Keyword/Domain Routing hoặc Boolean $\rightarrow$ Agent Mapping dưới bất kỳ hình thức nào.

---

## 1. Architecture Overview

```text
                                  USER QUERY
                                       │
                                       ▼
                             ┌──────────────────┐
                             │      TIER 0      │
                             │  Deterministic   │
                             │    Fast Path     │
                             └────────┬─────────┘
                                      │
                                 NOT HANDLED
                                      │
                                      ▼
                             ┌──────────────────┐
                             │      TIER 1      │
                             │  First-line      │
                             │  Solver & RAG    │
                             └────────┬─────────┘
                                      │
                             Requirement Assessment
                                      │
                                      ▼
                             ┌──────────────────┐
                             │   Tier1Result    │
                             │(required_caps)   │
                             └────────┬─────────┘
                                      │
                                      ▼
                             ┌──────────────────┐
                             │ EscalationPolicy │
                             │(Gap Evaluator)   │
                             └────────┬─────────┘
                                      │
                             ┌────────┴────────┐
                             │                 │
                          NO ESCALATE       ESCALATE
                             │                 │
                             ▼                 ▼
                          RESPONSE     EscalationDecision
                                      (unmet_capabilities)
                                               │
                                               ▼
                                       ┌──────────────────┐
                                       │CapabilityRegistry│
                                       │(Critical & Score)│
                                       └────────┬─────────┘
                                                │
                                       ┌────────┴────────┐
                                       │                 │
                                  MATCHED AGENT    NO SUITABLE AGENT
                                       │                 │
                                       ▼                 ▼
                               ┌───────────────┐ ┌───────────────┐
                               │    TIER 2     │ │ Safe Fallback │
                               │ Specialist    │ │ / Clarify     │
                               │ Agent         │ └───────────────┘
                               └───────────────┘
```

---

## 2. Responsibility Boundaries (Ranh giới Trách nhiệm)

| Component | Trách nhiệm Duy nhất | Quyết định Cốt lõi |
| :--- | :--- | :--- |
| **TIER 0** | Pure Code / DB Deterministic | *"Có xử lý chắc chắn bằng Pure Code / DB được không?"* |
| **TIER 1** | First-line Knowledge Solver & Assessor | *"Có thể trả lời bằng knowledge-grounded reasoning không?"* và bóc tách cụ thể `required_capabilities`. |
| **Tier1Result** | Capability Assessment Model | Chứa danh sách `required_capabilities` thực tế và các cờ metadata chẩn đoán (Diagnostic signals). |
| **EscalationPolicy** | Capability Gap Evaluator | Tính toán `unmet = required - TIER1_NATIVE_CAPABILITIES`. **KHÔNG tự tạo capability, KHÔNG phát hiện domain, KHÔNG mapping Boolean/Keyword $\rightarrow$ Agent**. |
| **CapabilityRegistry** | Critical & Coverage Matcher | *"Agent nào thỏa mãn tất cả Critical Capabilities và có điểm phủ (Coverage) >= threshold?"* |
| **TIER 2** | Specialist Execution Layer | Thực thi suy luận chuyên sâu & Tools DB cá nhân hóa, tái sử dụng `retrieved_documents` từ Tier 1 (Context Reuse). |

---

## 3. Data Contracts (`app/AI_agents/core/contract.py`)

### A. `CapabilityDefinition`
```python
class CapabilityDefinition(BaseModel):
    name: str
    tier: str = "tier2"
    critical: bool = False
    description: str = ""
```

### B. `Tier1Result`
```python
class Tier1Result(BaseModel):
    answer: str = ""
    evidence_sufficient: bool = True
    retrieval_confidence: float = 1.0
    
    # Diagnostic Metadata Signals (Chỉ làm metadata quan sát/observability, KHÔNG dùng để route hay sinh capability)
    requires_deep_reasoning: bool = False
    requires_multi_document_synthesis: bool = False
    requires_cross_domain_reasoning: bool = False
    requires_personal_analysis: bool = False
    requires_specialized_tools: bool = False
    safety_sensitive: bool = False
    
    # Concrete Required Capabilities (Danh sách Năng lực thực tế request yêu cầu)
    required_capabilities: List[str] = Field(default_factory=list)
    
    # Context Reuse cho Tier 2
    retrieved_documents: List[Any] = Field(default_factory=list)
    reasoning_context: Dict[str, Any] = Field(default_factory=dict)
```

### C. `EscalationDecision`
```python
class EscalationDecision(BaseModel):
    should_escalate: bool = False
    unmet_capabilities: List[str] = Field(default_factory=list)
    reasons: List[str] = Field(default_factory=list)
```

### D. `HandOffNotice`
```python
class HandOffNotice(BaseModel):
    source_agent: str = "tier1"
    target_agent_id: str
    reason: str
    original_query: str = ""
    required_capabilities: List[str] = Field(default_factory=list)
    payload: Dict[str, Any] = Field(default_factory=dict)
```

---

## 4. Tier 0 Implementation ([fast_extractor.py](file:///d:/ViT/BABYCARE/babycare-ai/app/AI_agents/core/fast_extractor.py))

Tier 0 giữ vai trò **Conservative Fast-Path**:
* Xử lý Pure Code/DB: Greeting xã giao, tra cứu nhanh cữ bú gần nhất, lần dùng thuốc gần nhất, tổng lượng sữa hôm nay, chiều cao cân nặng.
* Nếu là Mixed Query (vừa tra cứu vừa có câu thắc mắc/triệu chứng) $\rightarrow$ Trả về `handled = False` để chuyển sang Tier 1.

---

## 5. Tier 1 Implementation ([chat_graph.py](file:///d:/ViT/BABYCARE/babycare-ai/app/AI_agents/workflows/chat_graph.py))

Tier 1 là **First-line Solver mặc định cho mọi request không qua Tier 0**:
* Sử dụng Hybrid RAG + Reranker + LLM.
* Trả lời trực tiếp 100% các câu hỏi tri thức chuẩn WHO ở mọi miền (Dinh dưỡng, Y tế, Giấc ngủ, Tăng trưởng) nếu RAG đủ bằng chứng và không yêu cầu capability cá nhân hóa/tool.
* **KHÔNG đóng vai trò Router**: Tier 1 hoàn toàn không biết tên các Specialist Agent (`NutritionAgent`, `HealthAgent`).

---

## 6. Capability Assessment in Tier 1

Tier 1 thực hiện đánh giá nhu cầu năng lực của request và xuất ra `required_capabilities`:
* **Quy tắc**: `Requirement -> Capability` được phép; `Requirement -> Agent` không được phép.
* Ví dụ: Query *"Dựa trên lịch sử 14 ngày, phân tích tại sao bé tăng cân chậm"* $\rightarrow$ Tier 1 bóc tách `required_capabilities = ["feeding_history_access", "growth_history_access", "growth_nutrition_correlation", "temporal_pattern_analysis"]`.
* Cờ `requires_personal_analysis = True` và `requires_deep_reasoning = True` chỉ được ghi nhận làm **Diagnostic Signals** phục vụ Observability.

---

## 7. EscalationPolicy Implementation (`app/AI_agents/orchestrator/escalation_policy.py`)

`EscalationPolicy` **chỉ tính toán Capability Gap thuần túy**:

```python
TIER1_NATIVE_CAPABILITIES: Set[str] = {
    "knowledge_grounded_qa",
    "general_rag_retrieval",
    "standard_reasoning",
    "multi_document_synthesis"
}

class EscalationPolicy:
    def __init__(self, native_capabilities: Set[str] = None):
        self.native_capabilities = native_capabilities or TIER1_NATIVE_CAPABILITIES

    def evaluate(self, tier1_result: Tier1Result) -> EscalationDecision:
        required_set = set(tier1_result.required_capabilities or [])
        unmet = required_set - self.native_capabilities

        if not unmet:
            return EscalationDecision(
                should_escalate=False,
                unmet_capabilities=[],
                reasons=["all_capabilities_met_by_tier1"]
            )

        reasons = []
        if tier1_result.requires_personal_analysis:
            reasons.append("personalized_analysis_required")
        if tier1_result.requires_specialized_tools:
            reasons.append("specialized_tool_required")
        if tier1_result.requires_deep_reasoning:
            reasons.append("deep_reasoning_required")
        if tier1_result.requires_cross_domain_reasoning:
            reasons.append("cross_domain_analysis_required")
        if tier1_result.safety_sensitive:
            reasons.append("medical_safety_required")

        if not reasons:
            reasons.append("unmet_capability_required")

        return EscalationDecision(
            should_escalate=True,
            unmet_capabilities=list(unmet),
            reasons=reasons
        )
```

---

## 8. Capability Taxonomy

Định nghĩa độc lập hệ thống Capability Taxonomy không phụ thuộc vào tên Agent:
- **Tier 1 Native Capabilities**: `knowledge_grounded_qa`, `general_rag_retrieval`, `standard_reasoning`, `multi_document_synthesis`.
- **Specialized History Capabilities**: `feeding_history_access`, `growth_history_access`, `medication_history_access`, `symptom_history_access`.
- **Specialized Analysis Capabilities**: `growth_nutrition_correlation`, `temporal_pattern_analysis`, `symptom_severity_analysis`.
- **Specialized Execution & Safety Capabilities**: `structured_logging`, `fast_logging`, `medical_safety_eval`, `allergy_safety_eval`.

---

## 9. CapabilityRegistry Resolution & Critical Enforcement ([capability_registry.py](file:///d:/ViT/BABYCARE/babycare-ai/app/AI_agents/core/capability_registry.py))

```python
CRITICAL_CAPABILITIES: Set[str] = {
    "medical_safety_eval",
    "symptom_severity_analysis"
}

CAPABILITY_REGISTRY_CONFIG = {
    "min_coverage": 0.6  # Cấu hình ngưỡng coverage tối thiểu (Configurable)
}

class CapabilityRegistry:
    @classmethod
    def resolve_agent_by_capability(
        cls, 
        unmet_capabilities: List[str], 
        min_coverage: float = None
    ) -> Tuple[Optional[AgentContract], float]:
        if not unmet_capabilities:
            return None, 0.0

        threshold = min_coverage if min_coverage is not None else CAPABILITY_REGISTRY_CONFIG["min_coverage"]
        req_set = set(unmet_capabilities)
        req_critical = req_set.intersection(CRITICAL_CAPABILITIES)

        best_agent = None
        best_score = 0.0
        best_overlap_count = 0

        for agent in cls._agents.values():
            if not agent.capabilities:
                continue
            agent_cap_set = set(agent.capabilities)

            # STEP 1: RÀNG BUỘC CRITICAL CAPABILITY (Nếu thiếu critical capability -> Reject ngay)
            if req_critical and not req_critical.issubset(agent_cap_set):
                continue

            # STEP 2: TÍNH COVERAGE SCORE
            intersection = req_set.intersection(agent_cap_set)
            score = len(intersection) / len(req_set)

            # STEP 3: KIỂM TRA MINIMUM COVERAGE THRESHOLD
            if score >= threshold:
                if score > best_score or (score == best_score and len(intersection) > best_overlap_count):
                    best_score = score
                    best_overlap_count = len(intersection)
                    best_agent = agent

        # STEP 4: TRẢ VỀ AGENT PHÙ HỢP HOẶC NOSUITABLEAGENT (NONE)
        if best_agent:
            return best_agent, best_score

        return None, 0.0
```

---

## 10. Critical Capability Handling
* Nếu request yêu cầu `medical_safety_eval` (nằm trong `CRITICAL_CAPABILITIES`), chỉ Agent nào khai báo `medical_safety_eval` trong danh sách `capabilities` mới đủ điều kiện tham gia tính Coverage.
* Nếu Agent thiếu Critical Capability $\rightarrow$ Bị loại khỏi danh sách cân nhắc (Reject).

---

## 11. Minimum Coverage Configuration
* `min_coverage = 0.6` được đưa vào `CAPABILITY_REGISTRY_CONFIG` thay vì hardcode.
* Nếu điểm coverage của tất cả Agent đều $< 0.6$ $\rightarrow$ Trả về `NoSuitableAgent` (None).

---

## 12. Agent Capability Metadata Declarations

### A. `NutritionAgent` ([nutrition_graph.py](file:///d:/ViT/BABYCARE/babycare-ai/app/AI_agents/workflows/nutrition_graph.py))
```python
capabilities = [
    "feeding_history_access",
    "growth_history_access",
    "growth_nutrition_correlation",
    "temporal_pattern_analysis",
    "allergy_safety_eval"
]
```

### B. `HealthAgent` ([health_graph.py](file:///d:/ViT/BABYCARE/babycare-ai/app/AI_agents/workflows/health_graph.py))
```python
capabilities = [
    "medication_history_access",
    "symptom_history_access",
    "symptom_severity_analysis",
    "medical_safety_eval",
    "temporal_pattern_analysis"
]
```

### C. `VoiceLoggingAgent` ([voice_logging_graph.py](file:///d:/ViT/BABYCARE/babycare-ai/app/AI_agents/workflows/voice_logging_graph.py))
```python
capabilities = [
    "structured_logging",
    "fast_logging"
]
```

---

## 13. Master Orchestrator Flow ([agent_orchestrator.py](file:///d:/ViT/BABYCARE/babycare-ai/app/AI_agents/orchestrator/agent_orchestrator.py))

```python
# TIER 0
fast_result = FastTrackingExtractor.try_extract(message)
if fast_result and fast_result.get("handled"):
    return fast_result.get("response")

# TIER 1 (First-line Solver & Assessor)
tier1_result: Tier1Result = await self.chat_agent.solve(state)

# ESCALATION POLICY EVALUATION
decision: EscalationDecision = self.escalation_policy.evaluate(tier1_result)

if not decision.should_escalate:
    return tier1_result.answer

# CAPABILITY RESOLUTION IN REGISTRY
selected_agent, score = CapabilityRegistry.resolve_agent_by_capability(decision.unmet_capabilities)

if not selected_agent:
    logger.warning("[Orchestrator] NoSuitableAgent found for unmet capabilities. Safe fallback to Tier 1 grounded response.")
    return tier1_result.answer

# TIER 2 SPECIALIST EXECUTION WITH CONTEXT REUSE
return await selected_agent.execute_with_context(
    query=message,
    state=state,
    tier1_context=tier1_result.reasoning_context,
    retrieved_docs=tier1_result.retrieved_documents,
    escalation_decision=decision
)
```

---

## 14. Context Reuse
* Tier 2 **KHÔNG chạy lại** toàn bộ FAISS / BM25 / Reranker pipeline nếu `retrieved_documents` từ Tier 1 đã đủ.
* Tier 2 nhận `tier1_context` và chỉ bổ sung: DB Tools cá nhân hóa 14 ngày, phân tích tương quan tăng trưởng, đánh giá an toàn y tế.

---

## 15. Safe Fallback Handling
* Trường hợp `NoSuitableAgent` (do thiếu critical capability hoặc coverage $< 0.6$): Orchestrator tự động quay về sử dụng câu trả lời grounding an toàn từ Tier 1 (`tier1_result.answer`), kèm lời dặn phụ huynh tham khảo thêm ý kiến bác sĩ trực tiếp.

---

## 16. Unit Tests (10 Mandatory Test Cases)

1. **Test 1 — Generic Knowledge**: `"Trẻ 6 tháng nên ngủ bao nhiêu giờ?"` $\rightarrow$ Tier 1 tự trả lời trực tiếp.
2. **Test 2 — Nutrition Knowledge**: `"Bé 7 tháng có thể ăn trứng chưa?"` $\rightarrow$ Tier 1 tự trả lời trực tiếp (Không escalate chỉ vì từ "ăn/trứng").
3. **Test 3 — Personalized Nutrition**: `"Dựa trên lịch sử ăn 14 ngày, tại sao bé tăng cân chậm?"` $\rightarrow$ Unmet capabilities: `["feeding_history_access", "growth_history_access", "growth_nutrition_correlation", "temporal_pattern_analysis"]` $\rightarrow$ `NutritionAgent`.
4. **Test 4 — Personalized Medical**: `"Phân tích lịch sử sốt và thuốc 7 ngày của bé."` $\rightarrow$ Unmet capabilities: `["medication_history_access", "symptom_history_access", "symptom_severity_analysis", "medical_safety_eval"]` $\rightarrow$ `HealthAgent`.
5. **Test 5 — False Keyword Routing**: `"Tôi đang đọc bài viết về dinh dưỡng thể thao."` $\rightarrow$ Tier 1 tự trả lời (Không gọi `NutritionAgent`).
6. **Test 6 — Critical Capability Enforcement**: Request cần capability $A+B+C$ với $C$ là Critical. Agent 1 có $A+B$ (Coverage 66%) $\rightarrow$ Bị Reject do thiếu $C$.
7. **Test 7 — Coverage Scoring**: Required $A+B+C+D$. Agent A có 3/4 (75%), Agent B có 4/4 (100%) $\rightarrow$ Chọn Agent B.
8. **Test 8 — NoSuitableAgent Handling**: Không Agent nào đạt `min_coverage = 0.6` hoặc thiếu Critical Capability $\rightarrow$ Trả về `NoSuitableAgent` $\rightarrow$ Safe Fallback tại Tier 1.
9. **Test 9 — Boolean Independence**: Thay đổi `requires_personal_analysis = True` nhưng `required_capabilities = ["knowledge_grounded_qa"]` $\rightarrow$ KHÔNG tự động sinh capability mới, KHÔNG escalate.
10. **Test 10 — Context Reuse**: Kiểm tra Tier 2 tái sử dụng `retrieved_documents` từ Tier 1 mà không kích hoạt lại FAISS/BM25 search.

---

## 17. Integration Tests
* Kiểm tra luồng Server-Sent Events (SSE Stream) qua `run_agent_stream` đảm bảo các gói tin `step`, `tool_step`, `token` truyền mượt mà từ Tier 0 / Tier 1 / Tier 2 về Frontend.

---

## 18. Migration Steps (Chiến lược Chuyển đổi)
1. **Bước 1**: Cập nhật Data Contracts trong `contract.py` (`Tier1Result`, `EscalationDecision`, `AgentContract.capabilities`).
2. **Bước 2**: Khai báo `capabilities` danh sách công khai trên các Tier 2 Sub-Agents (`nutrition_graph.py`, `health_graph.py`, `voice_logging_graph.py`).
3. **Bước 3**: Xóa bỏ hoàn toàn mảng từ khóa cứng và hàm `detect_specialized_domain` trong `capability_registry.py`; thay thế bằng `resolve_agent_by_capability`.
4. **Bước 4**: Tạo module mới `escalation_policy.py`.
5. **Bước 5**: Refactor `ChatGraph` (`chat_graph.py`) thành First-line Solver trả về `Tier1Result`.
6. **Bước 6**: Cập nhật `AgentOrchestrator` (`agent_orchestrator.py`) kết nối luồng mới.

---

## 19. Files to MODIFY / NEW / DELETE

* **`[NEW]`** [escalation_policy.py](file:///d:/ViT/BABYCARE/babycare-ai/app/AI_agents/orchestrator/escalation_policy.py)
* **`[MODIFY]`** [contract.py](file:///d:/ViT/BABYCARE/babycare-ai/app/AI_agents/core/contract.py)
* **`[MODIFY]`** [capability_registry.py](file:///d:/ViT/BABYCARE/babycare-ai/app/AI_agents/core/capability_registry.py)
* **`[MODIFY]`** [agent_orchestrator.py](file:///d:/ViT/BABYCARE/babycare-ai/app/AI_agents/orchestrator/agent_orchestrator.py)
* **`[MODIFY]`** [chat_graph.py](file:///d:/ViT/BABYCARE/babycare-ai/app/AI_agents/workflows/chat_graph.py)
* **`[MODIFY]`** [nutrition_graph.py](file:///d:/ViT/BABYCARE/babycare-ai/app/AI_agents/workflows/nutrition_graph.py)
* **`[MODIFY]`** [health_graph.py](file:///d:/ViT/BABYCARE/babycare-ai/app/AI_agents/workflows/health_graph.py)
* **`[MODIFY]`** [voice_logging_graph.py](file:///d:/ViT/BABYCARE/babycare-ai/app/AI_agents/workflows/voice_logging_graph.py)
* **`[MODIFY]`** [out_of_scope_graph.py](file:///d:/ViT/BABYCARE/babycare-ai/app/AI_agents/workflows/out_of_scope_graph.py)

---

## 20. Acceptance Criteria (Tiêu chí Nghiệm thu)
* **Zero Keyword/Domain Routing**: Không có bất kỳ dòng lệnh `if "keyword" in query` hay `if domain == "nutrition"` nào dùng để trigger escalation.
* **Separation of Concerns**: Tier 1 chỉ giải quyết & đánh giá; EscalationPolicy chỉ tính Gap; CapabilityRegistry chỉ chọn Agent; Tier 2 tái sử dụng context.
* **100% Test Pass**: Tất cả 10 Test Cases (Test 1 đến Test 10) chạy qua thành công.


Nhóm 1: Kiểm thử Tier 0 — Pure Fast-Path (< 30ms, 0 Token LLM)
Mục tiêu: Đạt tốc độ tức thì, phản hồi xã giao hoặc tra cứu DB đơn giản mà không tốn chi phí LLM.

hi
chào em
cữ bú gần nhất
chiều cao cân nặng
🧠 Nhóm 2: Kiểm thử Tier 1 — First-line Knowledge Solver (RAG WHO, Không Leo Thang)
Mục tiêu: Tier 1 tự giải quyết thành công các câu hỏi tri thức y tế chuẩn WHO mà không cần gọi Specialist Agent.

Trẻ 6 tháng tuổi nên ngủ bao nhiêu giờ mỗi ngày?
Bé 7 tháng có thể ăn lòng đỏ trứng gà chưa?
Trẻ bị sốt nhẹ 37.8 độ thì phụ huynh nên chăm sóc như thế nào?
🥑 Nhóm 3: Kiểm thử Tier 2 — Nutrition Agent Escalation
Mục tiêu: Kích hoạt EscalationPolicy đòi hỏi Năng lực growth_history_access & growth_nutrition_correlation để gọi NutritionAgent.

Dựa trên lịch sử cữ ăn 14 ngày qua, tại sao bé Leo tăng cân chậm?
Phân tích biểu đồ tăng trưởng chiều cao cân nặng của bé trong 2 tuần qua.
🏥 Nhóm 4: Kiểm thử Tier 2 — Health Agent Escalation
Mục tiêu: Kích hoạt EscalationPolicy đòi hỏi Năng lực symptom_severity_analysis & medical_safety_eval để gọi HealthAgent.

Phân tích lịch sử sốt và các cữ uống thuốc Hapacol 7 ngày qua của bé.
Bé sốt lại sau 3 tiếng uống Hapacol 150mg, tôi có nên cho uống liều tiếp theo không?
🎙️ Nhóm 5: Kiểm thử Tier 0 / Tier 2 — Voice Logging Agent (Ghi nhật ký)
Mục tiêu: Trích xuất thông số và ghi trực tiếp vào cơ sở dữ liệu nhật ký của bé.

Bé vừa bú 150ml sữa công thức lúc 3 giờ chiều.
Vừa cho bé uống 1 gói Hapacol 150mg lúc 10h sáng.
🌐 Nhóm 6: Kiểm thử Tier 2 — Out of Scope Agent (Tra cứu Web)
Mục tiêu: Tự động phát hiện câu hỏi ngoài phạm vi chăm sóc trẻ em và gọi Web Search.

Cách làm món bún chả Hà Nội truyền thống chuẩn vị như thế nào?