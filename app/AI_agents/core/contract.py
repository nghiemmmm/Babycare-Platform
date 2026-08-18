from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

class CapabilityDefinition(BaseModel):
    """
    Metadata định nghĩa Năng lực (Capability) hệ thống.
    """
    name: str
    tier: str = "tier2"
    critical: bool = False
    description: str = ""

class Tier1Result(BaseModel):
    """
    Kết quả đánh giá từ Tier 1 First-line Solver.
    Tách biệt giữa Diagnostic Signals (Booleans) và Actual Capability Requirements.
    """
    answer: str = ""
    
    # Evidence & Grounding assessment
    evidence_sufficient: bool = True
    retrieval_confidence: float = 1.0
    
    # Diagnostic Metadata Signals (KHÔNG dùng trực tiếp để route hay sinh capability)
    requires_deep_reasoning: bool = False
    requires_multi_document_synthesis: bool = False
    requires_cross_domain_reasoning: bool = False
    requires_personal_analysis: bool = False
    requires_specialized_tools: bool = False
    safety_sensitive: bool = False
    
    # Concrete Required Capabilities (Danh sách Năng lực cụ thể do Tier 1 bóc tách từ request)
    required_capabilities: List[str] = Field(default_factory=list)
    
    # Context Reuse cho Tier 2
    retrieved_documents: List[Any] = Field(default_factory=list)
    reasoning_context: Dict[str, Any] = Field(default_factory=dict)

class EscalationDecision(BaseModel):
    """
    Quyết định leo thang từ EscalationPolicy dựa trên capability gap.
    """
    should_escalate: bool = False
    unmet_capabilities: List[str] = Field(default_factory=list)
    reasons: List[str] = Field(default_factory=list)

class HandOffNotice(BaseModel):
    """
    Payload cho Agent Hand-off.
    """
    source_agent: str = "tier1"
    target_agent_id: str
    reason: str
    original_query: str = ""
    required_capabilities: List[str] = Field(default_factory=list)
    payload: Dict[str, Any] = Field(default_factory=dict)

class AgentContract:
    """
    Runtime contract interface cho individual domain agents.
    Tự khai báo capabilities mà Agent sở hữu.
    """
    agent_id: str
    display_name: str
    description: str
    capabilities: List[str] = []
    intents: List[str] = []

    async def execute(self, state: dict) -> dict:
        """
        Thực thi mặc định của AgentContract.
        """
        raise NotImplementedError("AgentContract subclasses must implement execute()")

    async def execute_with_context(
        self,
        query: str,
        state: dict,
        tier1_context: Dict[str, Any],
        retrieved_docs: List[Any],
        escalation_decision: Optional[EscalationDecision] = None
    ) -> dict:
        """
        Thực thi chuyên sâu tái sử dụng Tier 1 Context (Context Reuse).
        Mặc định fallback về execute(state). Subclasses có thể override.
        """
        state["messages_context"] = tier1_context
        state["retrieved_docs"] = retrieved_docs
        state["rag_context_reused"] = True
        if tier1_context and isinstance(tier1_context, dict) and tier1_context.get("rag_context"):
            state["rag_context"] = tier1_context.get("rag_context")
        return await self.execute(state)

