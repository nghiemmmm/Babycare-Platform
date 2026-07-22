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
        # IMPORTANT: pass checkpointer to RouterGraph constructor so that
        # OutOfScopeGraph (and any subgraph using interrupt_before) is compiled
        # with the same checkpointer — enabling Human-in-the-Loop pauses.
        self.graph = RouterGraph(checkpointer=self.checkpointer).compile(
            checkpointer=self.checkpointer
        )

    async def run_agent(
        self,
        message: str,
        thread_id: str,
        baby_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Invokes the main AI agent graph asynchronously.

        If the graph hits an interrupt_before checkpoint (e.g. out_of_scope web_finalize),
        the result will have next != () and the caller should use resume_agent() to continue.
        """
        config = {
            "configurable": {
                "thread_id": thread_id,
                "user_id": user_id
            }
        }
        inputs = {
            "messages": [HumanMessage(content=message)],
            "baby_id": baby_id,
            "current_user_id": user_id
        }
        result = await self.graph.ainvoke(inputs, config=config)
        return result

    async def resume_agent(
        self,
        thread_id: str,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Resume a graph that was interrupted at an interrupt_before checkpoint.
        Called by the API after the frontend has reviewed the intermediate state
        (e.g. web search results for out_of_scope queries).

        Passes None as input to continue from the saved checkpoint without overriding state.
        """
        config = {
            "configurable": {
                "thread_id": thread_id,
                "user_id": user_id
            }
        }
        result = await self.graph.ainvoke(None, config=config)
        return result

    async def get_state(
        self,
        thread_id: str,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get the current state of a thread (useful after interrupt_before).
        Returns the state dict and the next node(s) to run.

        Example response when interrupted:
          {"next": ("web_finalize",), "values": {"web_search_results": [...], ...}}
        """
        config = {
            "configurable": {
                "thread_id": thread_id,
                "user_id": user_id
            }
        }
        state_snapshot = await self.graph.aget_state(config)
        return {
            "next": state_snapshot.next,
            "values": state_snapshot.values,
            "is_interrupted": bool(state_snapshot.next),
        }

