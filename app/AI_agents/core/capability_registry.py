from typing import Dict, Optional, Tuple, List, Set
import logging
from app.AI_agents.core.contract import AgentContract
from app.AI_agents.core.constant import CRITICAL_CAPABILITIES, CAPABILITY_REGISTRY_CONFIG

logger = logging.getLogger(__name__)

from langsmith import traceable

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
    @traceable(name="CapabilityRegistry.resolve_agent_by_capability")
    def resolve_agent_by_capability(
        cls,
        unmet_capabilities: List[str],
        min_coverage: Optional[float] = None
    ) -> Tuple[Optional[AgentContract], float]:
        """
        Phân giải và lựa chọn Specialist Agent phù hợp nhất dựa trên tỷ lệ bao phủ năng lực (Capability Coverage Score).

        Quy trình xử lý:
            1. Ràng buộc Critical Capabilities: Nếu request đòi hỏi năng lực y tế/an toàn cấp bách
               (như medical_safety_eval) mà Agent không sở hữu -> Loại bỏ ngay khỏi danh sách ứng viên.
            2. Tính toán Coverage Score: score = |required ∩ agent_capabilities| / |required|.
            3. Áp dụng Minimum Threshold: Chỉ chấp nhận các Agent có score >= min_coverage (mặc định 0.6).
            4. Deterministic Tie-Breaker: Chọn Agent có điểm cao nhất hoặc có số lượng năng lực khớp lớn nhất.

        Args:
            unmet_capabilities (List[str]): Danh sách các năng lực còn thiếu cần chuyên gia xử lý.
            min_coverage (Optional[float]): Ngưỡng bao phủ tối thiểu chấp nhận được (mặc định từ CAPABILITY_REGISTRY_CONFIG).

        Returns:
            Tuple[Optional[AgentContract], float]: Tuple gồm (Selected AgentContract, Coverage Score).
                Trả về (None, 0.0) nếu không có Agent nào đáp ứng đủ điều kiện (NoSuitableAgent).

        Raises:
            Không phát sinh ngoại lệ; tự động fallback an toàn về (None, 0.0) khi gặp lỗi hoặc danh sách trống.
        """
        if not unmet_capabilities:
            return None, 0.0

        threshold = min_coverage if min_coverage is not None else CAPABILITY_REGISTRY_CONFIG["min_coverage"]
        def _norm_cap(c: str) -> str:
            return str(c).lower().replace("capability_", "").strip()

        req_set = set(_norm_cap(c) for c in unmet_capabilities)
        crit_set = set(_norm_cap(c) for c in CRITICAL_CAPABILITIES)
        req_critical = req_set.intersection(crit_set)

        best_agent = None
        best_score = 0.0
        best_overlap_count = 0

        for agent in cls._agents.values():
            if not agent.capabilities:
                continue

            agent_cap_set = set(_norm_cap(c) for c in agent.capabilities)

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



