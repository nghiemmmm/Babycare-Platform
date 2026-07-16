from app.AI_agents.orchestrator.state_manager import FirestoreCheckpointer
from langchain_core.messages import HumanMessage
from typing import Optional, Dict, Any

class AgentOrchestrator:
    """
    Coordinator class to compile and run the central AI Agent RouterGraph.
    """
    def __init__(self):
        from app.AI_agents.workflows.router_graph import RouterGraph
        self.checkpointer = FirestoreCheckpointer()
        self.graph = RouterGraph().compile(checkpointer=self.checkpointer)

    async def run_agent(
        self,
        message: str,
        thread_id: str,
        baby_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Invokes the main AI agent graph asynchronously.
        """
        config = {"configurable": {"thread_id": thread_id}}
        inputs = {
            "messages": [HumanMessage(content=message)],
            "baby_id": baby_id,
            "current_user_id": user_id
        }
        result = await self.graph.ainvoke(inputs, config=config)
        return result
