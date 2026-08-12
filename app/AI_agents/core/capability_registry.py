from typing import Dict, Optional, Tuple, List, Set
import logging
from app.AI_agents.core.contract import AgentContract

logger = logging.getLogger(__name__)

# Cấu hình tập hợp Critical Capabilities (Thiếu critical cap -> Bị loại khỏi danh sách cân nhắc)
CRITICAL_CAPABILITIES: Set[str] = {
    "medical_safety_eval",
    "symptom_severity_analysis"
}

# Cấu hình ngưỡng Coverage tối thiểu (Configurable threshold)
CAPABILITY_REGISTRY_CONFIG = {
    "min_coverage": 0.6
}

class CapabilityRegistry:
    """
    Registry quản lý danh sách Agent và thực thi Specialist Resolution dựa trên
    Tỷ lệ Phủ Năng lực (Capability Coverage Score) & Ràng buộc Critical Capabilities.
    
    TUYỆT ĐỐI KHÔNG dùng từ khóa cứng (Keyword Matching) hay Domain Matching.
    """
    _agents: Dict[str, AgentContract] = {}

    @classmethod
    def register(cls, agent: AgentContract):
        cls._agents[agent.agent_id] = agent
        logger.info(f"[CapabilityRegistry] Registered agent '{agent.agent_id}' ({agent.display_name}) with capabilities: {agent.capabilities}")

    @classmethod
    def get_agent(cls, agent_id: str) -> Optional[AgentContract]:
        return cls._agents.get(agent_id)

    @classmethod
    def get_all_agents(cls) -> Dict[str, AgentContract]:
        return cls._agents

    @classmethod
    def resolve_agent_by_capability(
        cls,
        unmet_capabilities: List[str],
        min_coverage: Optional[float] = None
    ) -> Tuple[Optional[AgentContract], float]:
        """
        Phân giải Specialist Agent phù hợp nhất dựa trên danh sách capabilities chưa được đáp ứng:
        1. Critical Capability Constraint: Nếu request cần Critical Capability mà Agent không có -> Reject.
        2. Minimum Coverage Threshold: Phải đạt score >= min_coverage.
        3. Best Coverage & Deterministic Tie-Breaker.
        4. Trả về (None, 0.0) nếu NoSuitableAgent.
        """
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

            # STEP 1: RÀNG BUỘC CRITICAL CAPABILITY
            if req_critical and not req_critical.issubset(agent_cap_set):
                logger.info(f"[CapabilityRegistry] Rejecting agent '{agent.agent_id}': missing critical capabilities {req_critical - agent_cap_set}")
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

        if best_agent:
            logger.info(f"[CapabilityRegistry] Resolved agent '{best_agent.agent_id}' with coverage score {best_score:.2f} for unmet capabilities: {unmet_capabilities}")
            return best_agent, best_score

        logger.warning(f"[CapabilityRegistry] NoSuitableAgent found for unmet capabilities: {unmet_capabilities} (threshold: {threshold})")
        return None, 0.0

    @classmethod
    def evaluate_intent(cls, user_message: str, state: dict) -> Tuple[str, float]:
        """
        Mặc định tất cả các tin nhắn gửi vào phòng chat đều khởi đầu tại ChatAgent Central Gateway (Tier 1 Solver).
        """
        return ("chat_agent", 0.95)



