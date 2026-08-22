import logging
from typing import Set, List
from app.AI_agents.core.contract import Tier1Result, EscalationDecision
from app.AI_agents.core.constant import TIER1_NATIVE_CAPABILITIES

logger = logging.getLogger(__name__)

from langsmith import traceable

class EscalationPolicy:
    """
    EscalationPolicy duy nhất có trách nhiệm:
    "Xác định Tier 1 có đáp ứng được required_capabilities của request hay không."
    
    Tải tính toán Capability Gap = required_capabilities - TIER1_NATIVE_CAPABILITIES.
    KHÔNG tự tạo capability, KHÔNG phát hiện domain, KHÔNG mapping từ khóa hay Boolean sang Agent.
    """
    def __init__(self, native_capabilities: Set[str] = None):
        self.native_capabilities = native_capabilities or TIER1_NATIVE_CAPABILITIES

    @traceable(name="EscalationPolicy.evaluate")
    def evaluate(self, tier1_result: Tier1Result) -> EscalationDecision:
        """
        Đánh giá khoảng trống năng lực (Capability Gap) giữa yêu cầu của câu hỏi và năng lực native của Tier 1.

        Thuật toán:
            Capability Gap = required_capabilities - TIER1_NATIVE_CAPABILITIES
            - Nếu Gap rỗng: Tier 1 tự giải quyết toàn diện (should_escalate = False).
            - Nếu Gap có phần tử: Kích hoạt leo thang (should_escalate = True) và lập danh sách chẩn đoán.

        Args:
            tier1_result (Tier1Result): Đối tượng chứa kết quả phân tích yêu cầu từ Tier 1 ChatAgent.

        Returns:
            EscalationDecision: Quyết định leo thang gồm trạng thái should_escalate, 
                danh sách unmet_capabilities và các mã lý do chẩn đoán (reasons).

        Raises:
            Không phát sinh ngoại lệ; tự động trả về EscalationDecision(should_escalate=False) nếu tier1_result là None.
        """
        if not tier1_result:
            return EscalationDecision(should_escalate=False, unmet_capabilities=[], reasons=[])

        required_set = set(tier1_result.required_capabilities or [])
        
        # Capability Gap = Capabilities cần thiết - Capabilities native của Tier 1
        unmet_set = required_set - self.native_capabilities
        unmet_capabilities = list(unmet_set)

        if not unmet_capabilities:
            logger.info("[EscalationPolicy] All required capabilities are met natively by Tier 1. No escalation needed.")
            return EscalationDecision(
                should_escalate=False,
                unmet_capabilities=[],
                reasons=["all_capabilities_met_by_tier1"]
            )

        # Xây dựng danh sách lý do chẩn đoán dựa trên gap đã phát hiện
        reasons: List[str] = []
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

        logger.info(f"[EscalationPolicy] Escalation triggered! Unmet capabilities: {unmet_capabilities}. Reasons: {reasons}")
        return EscalationDecision(
            should_escalate=True,
            unmet_capabilities=unmet_capabilities,
            reasons=reasons
        )
