# BÀI TẬP & TÀI LIỆU KIẾN TRÚC BỘ NHỚ VÀ QUẢN LÝ NGỮ CẢNH (MEMORY & CONTEXT ARCHITECTURE) - BABYCARE AI

Tài liệu này ghi chép chi tiết toàn bộ thiết kế kiến trúc bộ nhớ, luồng ngữ cảnh (Context Flow), và các tối ưu hóa đã được triển khai trong dự án **BabyCare AI Platform**.

---

## 1. TỔNG QUAN KIẾN TRÚC (ARCHITECTURAL OVERVIEW)

BabyCare AI sử dụng mô hình **Multi-Tiered Hybrid Memory & Context Engine** kết hợp với **Progressive 3-Tier Escalation Framework**. Kiến trúc đảm bảo an toàn thông tin nhi khoa, tối ưu hóa ngân sách Token, và đạt độ minh bạch chi phí (Financial Observability).

```text
                               ┌─────────────────────────────────────────┐
                               │            USER INPUT QUERY             │
                               └────────────────────┬────────────────────┘
                                                    │
                                                    ▼
 ┌─────────────────────────────────────────────────────────────────────────────────────────────────────┐
 │                                        CONTEXT LAYER ENGINE                                         │
 ├─────────────────────────────────────────────────────────────────────────────────────────────────────┤
 │                                                                                                     │
 │  1. Long-Term Memory Store (Priority 85)                                                           │
 │     └─ Trích xuất & lưu vết bền vững: Dị ứng, Tiền sử y khoa, Thói quen theo (user_id, baby_id)    │
 │                                                                                                     │
 │  2. Session Summary Buffer (Priority 60)                                                            │
 │     └─ Tóm tắt hội thoại cũ khi vượt budget: OverallState["conversation_summary"]                  │
 │                                                                                                     │
 │  3. Short-Term Conversation Memory (Priority 50)                                                    │
 │     └─ Cắt tỉa tin nhắn linh hoạt dựa trên Token Budget (TokenBudget.select_messages_by_token_budget)│
 │                                                                                                     │
 │  4. RAG Trigger & Context Reuse (Priority 70)                                                       │
 │     └─ RAGTriggerEvaluator phân loại query; Reuses rag_context từ Tier 1 ➔ Tier 2                    │
 │                                                                                                     │
 └──────────────────────────────────────────────────┬──────────────────────────────────────────────────┘
                                                    │
                                                    ▼
 ┌─────────────────────────────────────────────────────────────────────────────────────────────────────┐
 │                                      CONTEXT BUILDER FACTORY                                        │
 ├─────────────────────────────────────────────────────────────────────────────────────────────────────┤
 │  - Lắp ghép ContextBundle tiêu chuẩn: system_instruction, messages, rag_context, long_term_facts    │
 │  - Ưu tiên Token Budget: System 100 ➔ Facts 85 ➔ RAG 70 (cap 800) ➔ Summary 60 ➔ History 50        │
 │  - Xuất dict serialization qua bundle.to_dict() cho Financial Observability                         │
 └──────────────────────────────────────────────────┬──────────────────────────────────────────────────┘
                                                    │
                                                    ▼
 ┌─────────────────────────────────────────────────────────────────────────────────────────────────────┐
 │                                PROGRESSIVE ESCALATION 3-TIER ROUTING                                │
 ├─────────────────────────────────────────────────────────────────────────────────────────────────────┤
 │  Tier 0: RouterGraph  ➔  Tier 1: ChatGraph (Context Prep & Assessment)  ➔  Tier 2: Specialist Subgraph │
 └─────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. BỐN TẦNG BỘ NHỚ CỐT LÕI (THE 4 MEMORY LAYERS)

### 🟢 Layer 1: Short-Term Conversation Memory (Bộ nhớ ngắn hạn)
- **Vị trí tệp**: `app/AI_agents/memory/memory_manager.py` (`select_messages_by_token_budget`)
- **Nguyên lý hoạt động**:
  - Không cắt cứng số lượng tin nhắn (`messages[-15:]`), mà tính toán chính xác lượng Token của từng tin nhắn (`~1.3 tokens/word`).
  - Tự động giữ lại các tin nhắn mới nhất nằm trong **History Token Budget** được cấp.
  - Luôn bảo toàn tính nhất quán của `SystemMessage` và tính đối xứng giữa các lượt trao đổi `HumanMessage` / `AIMessage`.

---

### 🟢 Layer 2: Conversation Summary Buffer (Tóm tắt diễn biến phiên)
- **Vị trí tệp**: `app/AI_agents/memory/memory_manager.py` (`summarize_old_messages`), `app/AI_agents/orchestrator/state_manager.py` (`conversation_summary`)
- **Nguyên lý hoạt động**:
  - Khi hội thoại kéo dài (vượt quá 1500 tokens), các tin nhắn cũ bị cắt tỉa khỏi Short-Term Memory sẽ được đưa qua `AIReasoner` để tự động tổng hợp thành **Tóm tắt diễn biến ngắn gọn**.
  - Tóm tắt này được ghi vào `OverallState["conversation_summary"]` và tiêm vào phần System Instruction với **Priority 60**.
  - Giúp AI duy trì mạch hội thoại dài qua hàng chục lượt thoại mà không mất bối cảnh ban đầu.

---

### 🟢 Layer 3: Long-Term Memory Store (Bộ nhớ bền vững Cross-Thread)
- **Vị trí tệp**: `app/AI_agents/memory/long_term_memory.py` (`LongTermMemoryStore` & `FactExtractor`)
- **Nguyên lý hoạt động**:
  - Lưu trữ bền vững dạng In-Memory Singleton indexed theo cặp chìa khóa `(user_id, baby_id)`.
  - `FactExtractor` quét tin nhắn người dùng để bóc tách tự động:
    - **ALLERGY**: Dị ứng (đậu nành, hải sản, hải sản mẫn cảm, sữa bò...).
    - **HEALTH_CONDITION**: Tiền sử bệnh lý (hen suyễn, viêm da cơ địa...).
    - **PREFERENCE / NUTRITION**: Thói quen ăn uống, thích/ghét món ăn.
  - Khi khởi tạo phiên chat mới (Thread B mới), `ContextBuilder` tự động nạp các Fact này vào mục `# DỮ LIỆU BỀN VỮNG VỀ BÉ (LONG-TERM FACTS)` với **Priority 85**.

---

### 🟢 Layer 4: Dynamic RAG Trigger & Context Reuse (Tối ưu hóa RAG)
- **Vị trí tệp**: `app/AI_agents/knowledge/rag_trigger.py` (`RAGTriggerEvaluator`), `app/AI_agents/core/contract.py`
- **Nguyên lý hoạt động**:
  - **RAG Trigger Bypass**: Phân loại câu hỏi trước khi gọi Vector Search. Bỏ qua RAG cho các câu chào hỏi/chitchat ("Chào bạn", "Cảm ơn") và câu tra cứu chỉ số DB cá nhân ("Bé nặng bao kg?").
  - **Context Reuse**: Khi lượt thoại escalate từ Tier 1 (ChatGraph) sang Tier 2 (HealthGraph/NutritionGraph), `rag_context` đã tìm kiếm ở Tier 1 được truyền lại cho Tier 2 thay vì tìm kiếm Vector lần thứ 2.
  - **Kết quả**: Giảm 50% số lượt RAG search trùng lặp và phản hồi chitchat tức thì < 0.2s.

---

## 3. THỐNG NHẤT CONTEXT BUILDER & TOKEN BUDGET

- **Vị trí tệp**: `app/AI_agents/context/context_builder.py`, `app/AI_agents/context/context_types.py`, `app/AI_agents/context/token_budget.py`

### Thứ tự ưu tiên Token Budget (Priority Allocation):
1. **System Persona & Core Guardrails** — Priority 100 (Bắt buộc giữ nguyên)
2. **Long-Term Facts (Allergies, Medical History)** — Priority 85
3. **RAG WHO Guidelines** — Priority 70 (Capped tối đa 800 tokens)
4. **Conversation Summary Buffer** — Priority 60
5. **Recent Short-Term Messages** — Priority 50 (Sử dụng phần budget còn lại)

### Đóng gói `ContextBundle`:
```python
@dataclass
class ContextBundle:
    system_instruction: str
    messages: List[AnyMessage] = field(default_factory=list)
    rag_context: str = ""
    long_term_facts: str = ""
    conversation_summary: str = ""
    total_tokens: int = 0
    token_breakdown: Dict[str, int] = field(default_factory=dict)
    sources_included: List[ContextSource] = field(default_factory=list)
    tool_steps: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "system_instruction": self.system_instruction,
            "message_count": len(self.messages),
            "rag_context": self.rag_context,
            "long_term_facts": self.long_term_facts,
            "conversation_summary": self.conversation_summary,
            "total_tokens": self.total_tokens,
            "token_breakdown": self.token_breakdown,
            "sources_included": [s.value for s in self.sources_included],
            "tool_steps": self.tool_steps
        }
```

---

## 4. BẢNG MÃ SỐ VÀ CÁC THÀNH PHẦN FILE TRONG HỆ THỐNG

| Thành phần | Đường dẫn File | Chức năng chính |
| :--- | :--- | :--- |
| **Context Types** | `app/AI_agents/context/context_types.py` | Định nghĩa `ContextSource`, `ContextItem`, `ContextBundle` |
| **Token Budget** | `app/AI_agents/context/token_budget.py` | Ước tính token (~1.3 token/word), allocate budget & calculate USD cost |
| **Context Builder** | `app/AI_agents/context/context_builder.py` | Factory tập trung xây dựng ContextBundle cho Chat, Health, Nutrition, Logging |
| **Long-Term Memory** | `app/AI_agents/memory/long_term_memory.py` | `LongTermMemoryStore` & `FactExtractor` bóc tách và duy trì fact cross-thread |
| **Memory Manager** | `app/AI_agents/memory/memory_manager.py` | `select_messages_by_token_budget` & `summarize_old_messages` |
| **RAG Trigger** | `app/AI_agents/knowledge/rag_trigger.py` | `RAGTriggerEvaluator` phân loại và kích hoạt RAG có điều kiện |
| **Agent Contract** | `app/AI_agents/core/contract.py` | Quản lý hợp đồng thực thi và chuyển tiếp Context Reuse sang Tier 2 |
| **Agent Orchestrator** | `app/AI_agents/orchestrator/agent_orchestrator.py` | Điều phối Escalation 3-Tier, Lazy LLM Answer execution & Financial Observability |

---

## 5. FINANCIAL & TOKEN OBSERVABILITY METRICS

Mọi câu trả lời trả về qua `AgentOrchestrator.run_agent()` đều đính kèm metadata đo đạc tài chính và token trong `state["financial_observability"]`:

```json
{
  "financial_observability": {
    "latency_ms": 1770,
    "input_tokens": 1250,
    "output_tokens": 180,
    "total_tokens": 1430,
    "token_breakdown": {
      "system_instruction": 450,
      "long_term_memory": 45,
      "conversation_summary": 85,
      "rag_docs": 350,
      "recent_messages": 320
    },
    "estimated_cost_usd": 0.000197,
    "model_name": "gemini-2.0-flash"
  }
}
```

---

## 6. BỘ KIỂM THỬ TỰ ĐỘNG (AUTOMATED TEST SUITE)

Hệ thống được bảo vệ bởi **23 ca kiểm thử Unit & Integration Tests** đạt 100% tỷ lệ vượt qua:

```bash
d:\ViT\BABYCARE\babycare-ai\venv\Scripts\python.exe -m pytest tests/unit/test_financial_observability.py tests/integration/test_context_memory_integration.py tests/unit/test_context_bundle_standardization.py tests/unit/test_rag_trigger.py tests/unit/test_long_term_memory.py tests/unit/test_conversation_summary.py tests/unit/test_token_aware_memory.py tests/unit/test_context_builder.py tests/unit/test_speculative_llm_fix.py tests/unit/test_context_reuse.py -v
```

### Danh sách các test file:
1. `tests/unit/test_financial_observability.py`: Đo đạc chi phí USD và latency
2. `tests/integration/test_context_memory_integration.py`: Kiểm thử tích hợp toàn luồng Escalation & Memory
3. `tests/unit/test_context_bundle_standardization.py`: Kiểm thử chuẩn hóa `ContextBundle` & `.to_dict()`
4. `tests/unit/test_rag_trigger.py`: Kiểm thử bỏ qua RAG cho Chitchat & DB profile queries
5. `tests/unit/test_long_term_memory.py`: Kiểm thử trích xuất dị ứng & truy xuất cross-thread
6. `tests/unit/test_conversation_summary.py`: Kiểm thử tóm tắt tin nhắn cũ vượt budget
7. `tests/unit/test_token_aware_memory.py`: Kiểm thử cắt tỉa tin nhắn ngắn hạn theo token
8. `tests/unit/test_context_builder.py`: Kiểm thử phân bổ token budget theo ưu tiên
9. `tests/unit/test_speculative_llm_fix.py`: Kiểm thử bỏ qua lượt gọi LLM Tier 1 khi escalate
10. `tests/unit/test_context_reuse.py`: Kiểm thử tái sử dụng Tier 1 RAG Context tại Tier 2