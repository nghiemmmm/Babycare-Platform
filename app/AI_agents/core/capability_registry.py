from typing import Dict, Optional, Tuple, List
import logging
from app.AI_agents.core.contract import AgentContract

logger = logging.getLogger(__name__)

class CapabilityRegistry:
    """
    Shared capability dictionary and lightweight classifier.
    Centralizes routing rules and intent evaluation to avoid hardcoded keyword logic in individual agents.
    """
    _agents: Dict[str, AgentContract] = {}

    @classmethod
    def register(cls, agent: AgentContract):
        cls._agents[agent.agent_id] = agent
        logger.info(f"[CapabilityRegistry] Registered agent '{agent.agent_id}' ({agent.display_name})")

    @classmethod
    def get_agent(cls, agent_id: str) -> Optional[AgentContract]:
        return cls._agents.get(agent_id)

    @classmethod
    def get_all_agents(cls) -> Dict[str, AgentContract]:
        return cls._agents

    @classmethod
    def evaluate_intent(cls, user_message: str, state: dict) -> Tuple[str, float]:
        """
        Shared lightweight evaluator combining Rule Engine and intent scoring.
        Returns Tuple[target_agent_id, confidence_score].
        """
        if not user_message:
            return ("chat_agent", 0.5)

        msg_lower = user_message.lower()

        # Health keywords -> HealthAgent
        health_keywords = ["sốt", "nhiệt độ", "hapacol", "thuốc", "bệnh", "bác sĩ", "ho", "sổ mũi", "co giật", "triệu chứng", "ốm", "đau"]
        if any(k in msg_lower for k in health_keywords):
            return ("health_agent", 0.95)

        # Activity logging keywords -> VoiceLoggingAgent
        logging_keywords = ["ghi nhận", "lưu lịch", "vừa uống", "vừa ăn", "vừa đo", "nhật ký cữ"]
        if any(k in msg_lower for k in logging_keywords):
            return ("voice_logging_agent", 0.95)

        # Nutrition & Growth keywords -> NutritionAgent
        nutrition_keywords = ["ăn", "sữa", "bú", "cháo", "bột", "dinh dưỡng", "cân nặng", "chiều cao", "whos", "thực đơn", "ăn dặm", "dị ứng"]
        if any(k in msg_lower for k in nutrition_keywords):
            return ("nutrition_agent", 0.90)

        # Out-of-scope keywords -> OutOfScopeAgent
        out_of_scope_keywords = ["thời tiết", "bóng đá", "chính trị", "chứng khoán", "tin tức", "xem phim"]
        if any(k in msg_lower for k in out_of_scope_keywords):
            return ("out_of_scope_agent", 0.90)

        # Baseline fallback -> ChatAgent
        return ("chat_agent", 0.75)
