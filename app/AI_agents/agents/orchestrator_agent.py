"""
OrchestratorAgent - Agent-level wrapper
========================================
Chịu trách nhiệm phân loại ý định (intent classification) của người dùng.
Không điều phối đồ thị LangGraph — đó là nhiệm vụ của AgentOrchestrator 
trong orchestrator/agent_orchestrator.py.
"""
from app.AI_agents.agents.base_agent import BaseAgent
from app.AI_agents.orchestrator.task_planner import TaskPlanner


class OrchestratorAgent(BaseAgent):
    """
    Agent chuyên phân loại ý định người dùng.
    Dùng trong unit tests hoặc khi cần gọi intent classifier trực tiếp
    mà không cần khởi động toàn bộ RouterGraph.

    Để chạy toàn bộ AI Agent pipeline, hãy dùng:
        app.AI_agents.orchestrator.agent_orchestrator.AgentOrchestrator
    """
    def __init__(self):
        super().__init__(name="OrchestratorAgent")
        self.planner = TaskPlanner()

    async def plan_and_route(self, state: dict) -> dict:
        """Classify intent from state and return next routing step."""
        return await self.planner.aclassify_intent(state)
