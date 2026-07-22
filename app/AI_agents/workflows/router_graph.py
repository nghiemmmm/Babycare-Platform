from langgraph.graph import StateGraph, START, END
from app.AI_agents.orchestrator.state_manager import OverallState
from app.AI_agents.orchestrator.task_planner import TaskPlanner
from app.AI_agents.workflows.voice_logging_graph import VoiceLoggingGraph
from app.AI_agents.workflows.chat_graph import ChatGraph
from app.AI_agents.workflows.cry_analysis_graph import CryAnalysisGraph
from app.AI_agents.workflows.report_graph import ReportGraph
from app.AI_agents.workflows.health_graph import HealthGraph
from app.AI_agents.workflows.nutrition_graph import NutritionGraph
from app.AI_agents.workflows.out_of_scope_graph import OutOfScopeGraph
from langchain_core.messages import AIMessage

class RouterGraph:
    def __init__(self, checkpointer=None):
        self.planner = TaskPlanner()
        self.voice_logging_graph = VoiceLoggingGraph().compile()
        self.chat_graph = ChatGraph().compile()
        self.cry_analysis_graph = CryAnalysisGraph().compile()
        self.report_graph = ReportGraph().compile()
        self.health_graph = HealthGraph().compile()
        self.nutrition_graph = NutritionGraph().compile()
        # Out-of-scope graph uses checkpointer + interrupt_before=["web_finalize"]
        self.out_of_scope_graph = OutOfScopeGraph().compile(checkpointer=checkpointer)

    async def classify_intent_node(self, state: OverallState) -> dict:
        """Classify user query intent."""
        return await self.planner.aclassify_intent(state)

    def compile(self, checkpointer=None):
        """Compile the main state graph routing logic."""
        builder = StateGraph(OverallState)
        
        # Add nodes
        builder.add_node("classify_intent", self.classify_intent_node)
        builder.add_node("chat_subgraph", self.chat_graph)
        builder.add_node("voice_logging_subgraph", self.voice_logging_graph)
        builder.add_node("cry_analysis_subgraph", self.cry_analysis_graph)
        builder.add_node("health_subgraph", self.health_graph)
        builder.add_node("nutrition_subgraph", self.nutrition_graph)
        builder.add_node("report_subgraph", self.report_graph)
        builder.add_node("out_of_scope_subgraph", self.out_of_scope_graph)

        # Edges
        builder.add_edge(START, "classify_intent")
        
        # Routing function
        def route_intent(state: OverallState) -> str:
            intent = state.get("extracted_intent", "chat")
            mapping = {
                "chat": "chat_subgraph",
                "log_activity": "voice_logging_subgraph",
                "analyze_cry": "cry_analysis_subgraph",
                "check_health": "health_subgraph",
                "check_nutrition": "nutrition_subgraph",
                "generate_report": "report_subgraph",
                "out_of_scope": "out_of_scope_subgraph",
            }
            return mapping.get(intent, "chat_subgraph")

        builder.add_conditional_edges(
            "classify_intent",
            route_intent,
            {
                "chat_subgraph": "chat_subgraph",
                "voice_logging_subgraph": "voice_logging_subgraph",
                "cry_analysis_subgraph": "cry_analysis_subgraph",
                "health_subgraph": "health_subgraph",
                "nutrition_subgraph": "nutrition_subgraph",
                "report_subgraph": "report_subgraph",
                "out_of_scope_subgraph": "out_of_scope_subgraph",
            }
        )

        # End transitions
        builder.add_edge("chat_subgraph", END)
        builder.add_edge("voice_logging_subgraph", END)
        builder.add_edge("cry_analysis_subgraph", END)
        builder.add_edge("health_subgraph", END)
        builder.add_edge("nutrition_subgraph", END)
        builder.add_edge("report_subgraph", END)
        builder.add_edge("out_of_scope_subgraph", END)

        return builder.compile(checkpointer=checkpointer)
