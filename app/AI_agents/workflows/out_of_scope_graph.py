import logging
from datetime import datetime, timezone
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import AIMessage

from app.AI_agents.orchestrator.state_manager import OverallState
from app.AI_agents.tools.implementation.web_search_tool import WebSearchTool
from app.AI_agents.core.constant import OUT_OF_SCOPE_SYSTEM_PROMPT
from app.AI_agents.core.reasoner import AIReasoner

logger = logging.getLogger(__name__)


class OutOfScopeGraph:
    """
    LangGraph subgraph for handling out-of-scope queries.

    Flow:
        START -> web_search -> [interrupt_before] -> web_finalize -> END

    The interrupt_before="web_finalize" checkpoint allows the API/frontend to:
    - Review the raw web search results before finalizing the response
    - Inject additional context or human feedback before the LLM generates the answer
    - Resume the graph to produce the final user-facing response
    """

    def __init__(self):
        self.web_search_tool = WebSearchTool()
        self.reasoner = AIReasoner(model_name="gemini-flash-latest")

    async def web_search_node(self, state: OverallState) -> dict:
        """
        Node 1: Run web search using Tavily (primary) or DuckDuckGo (fallback).
        Extracts the user query from the last message and searches the web.
        """
        messages = state.get("messages", [])
        query = ""
        for msg in reversed(messages):
            if hasattr(msg, "type") and msg.type == "human":
                query = msg.content
                break
            elif hasattr(msg, "role") and msg.role == "user":
                query = msg.content
                break

        if not query:
            query = messages[-1].content if messages else "general search"

        logger.info(f"[OutOfScope] web_search_node: query='{query}'")

        import asyncio
        search_result = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: self.web_search_tool._run(query, max_results=3)
        )

        logger.info(
            f"[OutOfScope] web_search_node: provider={search_result.get('provider')}, "
            f"results={len(search_result.get('results', []))}"
        )

        return {
            "web_search_results": search_result.get("results", []),
            "is_out_of_scope": True,
        }

    async def web_finalize_node(self, state: OverallState) -> dict:
        """
        Node 2 (after interrupt): Synthesize web search results into a user-friendly response.
        Uses the LLM to summarize and contextualize the web search output.
        """
        messages = state.get("messages", [])
        web_results = state.get("web_search_results", [])

        # Format web results for the prompt
        if web_results:
            formatted_results = "\n\n".join([
                f"**{r.get('title', 'Ket qua')}**\n{r.get('snippet', '')}"
                + (f"\nNguon: {r['url']}" if r.get("url") else "")
                for r in web_results
            ])
        else:
            formatted_results = "Khong tim thay ket qua web phu hop."

        system_prompt = OUT_OF_SCOPE_SYSTEM_PROMPT.format(web_results=formatted_results)

        logger.info("[OutOfScope] web_finalize_node: generating response with LLM")

        try:
            # Extract last user message as the prompt for the reasoner
            user_prompt = ""
            for msg in reversed(messages):
                if hasattr(msg, "type") and msg.type == "human":
                    user_prompt = msg.content
                    break
                elif hasattr(msg, "role") and msg.role == "user":
                    user_prompt = msg.content
                    break
            if not user_prompt and messages:
                user_prompt = messages[-1].content

            response_text = await self.reasoner.areason(
                prompt=user_prompt,
                system_instruction=system_prompt,
            )
        except Exception as e:
            logger.error(f"[OutOfScope] web_finalize_node LLM error: {e}")
            # Graceful fallback: return raw search results
            snippets = [r.get("snippet", "") for r in web_results if r.get("snippet")]
            response_text = (
                "Cau hoi nay nam ngoai pham vi chuyen mon cua BabyCare AI.\n\n"
                + "\n\n".join(snippets[:2])
                + "\n\nHay hoi toi ve cham soc be nhe! 👶"
            )


        return {
            "messages": [AIMessage(content=response_text, response_metadata={"created_at": datetime.now(timezone.utc).isoformat()})],
        }

    def compile(self, checkpointer=None, interrupt_before=None):
        """
        Compile the out-of-scope subgraph.

        Args:
            checkpointer: LangGraph checkpointer (e.g. FirestoreCheckpointer).
            interrupt_before: Defaults to ["web_finalize"] for human-in-the-loop.
        """
        if interrupt_before is None:
            interrupt_before = ["web_finalize"]

        builder = StateGraph(OverallState)

        builder.add_node("web_search", self.web_search_node)
        builder.add_node("web_finalize", self.web_finalize_node)

        builder.add_edge(START, "web_search")
        builder.add_edge("web_search", "web_finalize")
        builder.add_edge("web_finalize", END)

        return builder.compile(
            checkpointer=checkpointer,
            interrupt_before=interrupt_before,
        )
