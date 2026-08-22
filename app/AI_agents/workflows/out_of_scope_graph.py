import asyncio
import logging
import time 
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
        from app.AI_agents.core.constant import OUT_OF_SCOPE_MODEL, OUT_OF_SCOPE_PROVIDER
        self.web_search_tool = WebSearchTool()
        self.reasoner = AIReasoner(model_name=OUT_OF_SCOPE_MODEL, provider=OUT_OF_SCOPE_PROVIDER)

    async def web_search_node(self, state: OverallState) -> dict:
        """
        Node 1: Thực hiện tìm kiếm thông tin mở rộng trên Web (Tavily Search / DuckDuckGo).

        Args:
            state (OverallState): Trạng thái hội thoại chứa câu hỏi người dùng và tool_steps.

        Returns:
            dict: Cập nhật state chứa web_search_results (danh sách kết quả web), cờ is_out_of_scope=True và tool_steps.

        Raises:
            Không phát sinh ngoại lệ; tự động fallback về kết quả rỗng nếu lỗi mạng hoặc hết hạn API search.
        """
        from app.AI_agents.utils.helpers import extract_user_query, build_tool_step, calculate_elapsed_ms
        query = extract_user_query(state) or "general search"

        logger.info(f"[OutOfScope] web_search_node: query='{query}'")

        t0 = time.time()
        search_result = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: self.web_search_tool._run(query, max_results=3)
        )
        results = search_result.get("results", [])
        provider = search_result.get("provider", "web")

        logger.info(
            f"[OutOfScope] web_search_node: provider={provider}, "
            f"results={len(results)}"
        )

        step = build_tool_step(
            tool_name="WebSearchTool",
            display_name="Tìm kiếm thông tin mở rộng (Web Search)",
            args={"query": query, "provider": provider},
            result_summary=f"Đã thu thập {len(results)} kết quả từ nguồn web ({provider})",
            duration_ms=calculate_elapsed_ms(t0)
        )

        return {
            "web_search_results": results,
            "is_out_of_scope": True,
            "tool_steps": [step]
        }

    async def web_finalize_node(self, state: OverallState) -> dict:
        """
        Node 2: Tổng hợp và định dạng kết quả tìm kiếm web thành câu trả lời tự nhiên, thân thiện và ấm áp cho phụ huynh.

        Args:
            state (OverallState): Trạng thái hội thoại chứa web_search_results và messages.

        Returns:
            dict: Cập nhật state gồm danh sách messages phản hồi từ AI Agent (AIMessage).

        Raises:
            Không phát sinh ngoại lệ; tự động trả về phản hồi an toàn nếu quá trình tổng hợp LLM bị lỗi.
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

from app.AI_agents.core.contract import AgentContract

from langsmith import traceable

class OutOfScopeAgentContract(AgentContract):
    agent_id = "out_of_scope_agent"
    display_name = "Web Search & General Out-Of-Scope Agent"
    description = "Tìm kiếm thông tin tổng hợp trên mạng cho các câu hỏi nằm ngoài phạm vi nhi khoa."
    capabilities = [
        "out_of_scope_handling",
        "web_search",
        "CAPABILITY_WEB_SEARCH"
    ]
    intents = ["out_of_scope"]

    def __init__(self, checkpointer=None):
        self.graph = OutOfScopeGraph().compile(checkpointer=checkpointer, interrupt_before=[])

    @traceable(name="Tier3.OutOfScopeAgent.execute")
    async def execute(self, state: dict, config: dict = None) -> dict:
        thread_id = state.get("thread_id") or "thread_out_of_scope_default"
        cfg = config or {"configurable": {"thread_id": thread_id}}
        return await self.graph.ainvoke(state, config=cfg)

    @traceable(name="Tier3.OutOfScopeAgent.execute_with_context")
    async def execute_with_context(
        self,
        query: str,
        state: dict,
        tier1_context: str = None,
        retrieved_docs: list = None,
        escalation_decision=None,
        config: dict = None
    ) -> dict:
        from langchain_core.messages import HumanMessage
        thread_id = state.get("thread_id") or "thread_out_of_scope_default"
        cfg = config or {"configurable": {"thread_id": thread_id}}
        exec_state = {
            "messages": state.get("messages", [HumanMessage(content=query)]),
            "baby_id": state.get("baby_id"),
            "current_user_id": state.get("current_user_id"),
            "tool_steps": state.get("tool_steps", []),
            "next_step": "out_of_scope_agent"
        }
        return await self.graph.ainvoke(exec_state, config=cfg)



