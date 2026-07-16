from unittest.mock import patch, MagicMock, AsyncMock
import pytest
from app.AI_agents.core.reasoner import AIReasoner
from app.AI_agents.models.llm_factory import LLMFactory
from app.AI_agents.models.model_router import ModelRouter

def test_ai_reasoner_sync():
    with patch("app.AI_agents.core.reasoner.ChatGoogleGenerativeAI") as mock_chat:
        mock_instance = MagicMock()
        mock_chat.return_value = mock_instance
        mock_instance.invoke.return_value.content = "Mock response"
        
        reasoner = AIReasoner()
        result = reasoner.reason("Hello")
        assert result == "Mock response"
        mock_instance.invoke.assert_called_once()

@pytest.mark.anyio
async def test_ai_reasoner_async():
    with patch("app.AI_agents.core.reasoner.ChatGoogleGenerativeAI") as mock_chat:
        mock_instance = MagicMock()
        mock_chat.return_value = mock_instance
        
        async def mock_ainvoke(messages):
            mock_res = MagicMock()
            mock_res.content = "Mock async response"
            return mock_res
            
        mock_instance.ainvoke = mock_ainvoke
        
        reasoner = AIReasoner()
        result = await reasoner.areason("Hello")
        assert result == "Mock async response"

from app.core.config import settings

def test_model_router():
    with patch("app.AI_agents.models.llm_factory.ChatGoogleGenerativeAI") as mock_chat:
        model = ModelRouter.get_model_for_task("simple query")
        mock_chat.assert_called_with(model="gemini-2.5-flash", google_api_key=settings.GEMINI_API_KEY, temperature=0.0)

        ModelRouter.get_model_for_task("complex reasoning or summary report")
        mock_chat.assert_called_with(model="gemini-1.5-pro", google_api_key=settings.GEMINI_API_KEY, temperature=0.0)

from app.AI_agents.workflows.router_graph import RouterGraph
from langchain_core.messages import HumanMessage

@pytest.mark.anyio
async def test_router_graph_routing():
    router_graph = RouterGraph()
    chain = router_graph.compile()
    assert chain is not None

    with patch("app.AI_agents.orchestrator.task_planner.TaskPlanner.aclassify_intent") as mock_classify:
        mock_classify.return_value = {"extracted_intent": "log_activity", "next_step": "log_activity"}
        
        with patch("app.AI_agents.core.reasoner.AIReasoner.areason") as mock_reason:
            mock_reason.return_value = '{"activity_type": "feeding", "data": {"food_name": "sữa", "amount_g": 120.0}}'
            
            with patch("app.AI_agents.tools.implementation.nutrition_tools.NutritionTrackingTool._run") as mock_run:
                mock_run.return_value = "Success"
                
                result = await chain.ainvoke(
                    {
                        "messages": [HumanMessage(content="Bé ăn sữa 120ml lúc 8h")],
                        "baby_id": "baby-123",
                        "current_user_id": "user-123"
                    }
                )
                assert "messages" in result
                assert "Đã ghi nhận cữ ăn dặm của bé: sữa với lượng 120.0g thành công." in result["messages"][-1].content

from app.AI_agents.workflows.voice_logging_graph import VoiceLoggingGraph

@pytest.mark.anyio
async def test_voice_logging_graph():
    logging_graph = VoiceLoggingGraph()
    chain = logging_graph.compile()

    with patch("app.AI_agents.core.reasoner.AIReasoner.areason") as mock_reason:
        mock_reason.return_value = '{"activity_type": "feeding", "data": {"food_name": "sữa bột", "amount_g": 150.0}}'

        with patch("app.AI_agents.tools.implementation.nutrition_tools.NutritionTrackingTool._run") as mock_run:
            mock_run.return_value = "Mocked solid food log created"

            result = await chain.ainvoke(
                {
                    "messages": [HumanMessage(content="Bé bú 150ml sữa bột")],
                    "baby_id": "test-baby-id",
                    "current_user_id": "test-user-id"
                }
            )

            assert "messages" in result
            assert "Đã ghi nhận cữ ăn dặm của bé: sữa bột với lượng 150.0g thành công." in result["messages"][-1].content
            mock_run.assert_called_once()
            call_kwargs = mock_run.call_args[1]
            assert call_kwargs["baby_id"] == "test-baby-id"
            assert call_kwargs["user_id"] == "test-user-id"
            assert call_kwargs["data"]["food_name"] == "sữa bột"
            assert call_kwargs["data"]["amount_g"] == 150.0

from app.AI_agents.workflows.chat_graph import ChatGraph
from app.modules.baby.schemas import BabyResponse
from app.modules.growth_tracking.schemas import GrowthLogResponse

@pytest.mark.anyio
async def test_chat_graph():
    chat_graph = ChatGraph()
    chain = chat_graph.compile()
    assert chain is not None

    with patch("app.modules.baby.service.BabyService.get_baby_by_id") as mock_get_baby:
        mock_get_baby.return_value = BabyResponse(
            name="Bo",
            birth_date="2026-01-01",
            gender="boy",
            guardians=["user-123"],
            created_at="2026-01-01T00:00:00Z",
            updated_at="2026-01-01T00:00:00Z"
        )
        
        with patch("app.modules.growth_tracking.service.GrowthTrackingService.get_growth_history") as mock_growth:
            mock_growth.return_value = [
                GrowthLogResponse(
                    height=70.0,
                    weight=8.5,
                    head_circumference=None,
                    logged_at="2026-07-01T00:00:00Z"
                )
            ]
            
            with patch("app.AI_agents.core.reasoner.AIReasoner.areason") as mock_reason:
                mock_reason.return_value = "Xin chào mẹ của bé Bo, bé Bo trộm vía đang phát triển rất tốt."

                result = await chain.ainvoke(
                    {
                        "messages": [HumanMessage(content="Chào trợ lý")],
                        "baby_id": "baby-123",
                        "current_user_id": "user-123"
                    }
                )
                
                assert "messages" in result
                assert "Bo" in result["messages"][-1].content

from app.AI_agents.tools.implementation.rag_tools import KnowledgeRetrievalTool
from app.AI_agents.workflows.cry_analysis_graph import CryAnalysisGraph
from app.AI_agents.knowledge.rag_pipeline import FakeEmbeddings

def test_knowledge_retrieval_tool():
    with patch("app.AI_agents.knowledge.rag_pipeline.GoogleGenerativeAIEmbeddings", return_value=FakeEmbeddings()):
        tool = KnowledgeRetrievalTool()
        context = tool._run("Trẻ quấy khóc")
        assert "tã bẩn" in context or "quấy khóc" in context

@pytest.mark.anyio
async def test_cry_analysis_graph():
    graph = CryAnalysisGraph()
    chain = graph.compile()
    assert chain is not None

    with patch("app.AI_agents.core.reasoner.AIReasoner.areason") as mock_reason:
        mock_reason.return_value = "Bé có vẻ đói do tiếng khóc hungry kéo dài."

        result = await chain.ainvoke(
            {
                "messages": [HumanMessage(content="Bé đang khóc")],
                "baby_id": "baby-123",
                "current_user_id": "user-123",
                "extracted_data": {"audio_file": "hungry_cry_baby.wav"}
            }
        )

        assert "messages" in result
        assert "hungry" in result["messages"][-1].content
        assert "Bé có vẻ đói" in result["messages"][-1].content

from app.AI_agents.workflows.report_graph import ReportGraph
from app.AI_agents.orchestrator.state_manager import FirestoreCheckpointer

@pytest.mark.anyio
async def test_report_graph():
    graph = ReportGraph()
    chain = graph.compile()
    assert chain is not None

    with patch("app.modules.baby.service.BabyService.get_baby_by_id") as mock_baby:
        mock_baby.return_value = MagicMock(name="Bo", birth_date="2026-01-01", gender="boy")

        with patch("app.AI_agents.core.reasoner.AIReasoner.areason") as mock_reason:
            mock_reason.return_value = "Báo cáo: Bé phát triển tốt."

            with patch("app.AI_agents.workflows.report_graph.generate_pdf_report") as mock_pdf:
                result = await chain.ainvoke(
                    {
                        "messages": [HumanMessage(content="Hãy tạo báo cáo tuần này")],
                        "baby_id": "baby-123",
                        "current_user_id": "user-123"
                    }
                )
                assert "messages" in result
                assert "Báo cáo: Bé phát triển tốt." in result["messages"][-1].content
                mock_pdf.assert_called_once()

def test_firestore_checkpointer():
    with patch("app.AI_agents.orchestrator.state_manager.get_firestore_db") as mock_db:
        db_instance = MagicMock()
        mock_db.return_value = db_instance
        
        checkpointer = FirestoreCheckpointer()
        assert checkpointer.db == db_instance

from app.modules.ai_agent.router import chat_with_agent, ChatRequest
from app.modules.auth.schemas import UserRecord
from langchain_core.messages import AIMessage

@pytest.mark.anyio
async def test_chat_with_agent_endpoint():
    req = ChatRequest(
        message="Bé bị sốt",
        baby_id="baby-123",
        thread_id="thread-123"
    )
    user = UserRecord(
        uid="user-123",
        email="test@example.com",
        name="Parent",
        picture=None
    )
    
    with patch("app.AI_agents.orchestrator.state_manager.FirestoreCheckpointer") as mock_cp:
        mock_cp_instance = MagicMock()
        mock_cp.return_value = mock_cp_instance
        
        with patch("app.AI_agents.workflows.router_graph.RouterGraph.compile") as mock_compile:
            mock_chain = MagicMock()
            mock_compile.return_value = mock_chain
            
            mock_chain.ainvoke = AsyncMock(return_value={
                "messages": [AIMessage(content="Mocked response content")],
                "next_step": "chat"
            })
            
            res = await chat_with_agent(req, current_user=user)
            
            assert res.response == "Mocked response content"
            assert res.next_step == "chat"

from app.AI_agents.agents import BaseAgent, OrchestratorAgent, ResearchAgent, ToolExecutorAgent

@pytest.mark.anyio
async def test_agent_abstractions():
    agent = BaseAgent("TestAgent")
    with patch("app.AI_agents.core.reasoner.AIReasoner.areason") as mock_reason:
        mock_reason.return_value = "Agent response"
        res = await agent.run("Hello")
        assert res == "Agent response"

    orch = OrchestratorAgent()
    with patch("app.AI_agents.orchestrator.task_planner.TaskPlanner.aclassify_intent") as mock_intent:
        mock_intent.return_value = {"intent": "chat"}
        res = await orch.plan_and_route({})
        assert res == {"intent": "chat"}

    with patch("app.AI_agents.knowledge.rag_pipeline.GoogleGenerativeAIEmbeddings", return_value=FakeEmbeddings()):
        research = ResearchAgent()
        with patch("app.AI_agents.knowledge.retriever.MedicalRetriever.retrieve_context") as mock_retrieve:
            mock_retrieve.return_value = "retrieved context"
            res = research.search("query")
            assert res == "retrieved context"

    executor = ToolExecutorAgent()
    with patch("app.AI_agents.tools.implementation.nutrition_tools.NutritionTrackingTool._run") as mock_tool:
        mock_tool.return_value = "nutrition logged"
        res = executor.execute("nutrition", "add", baby_id="1", user_id="2", data={})
        assert res == "nutrition logged"

from app.AI_agents.core import agent_config, get_agent_logger, AIAgentException

def test_core_utilities():
    assert agent_config.DEFAULT_CHAT_MODEL == "gemini-2.5-flash"
    assert agent_config.RAG_CHUNK_SIZE == 500
    
    logger = get_agent_logger("test")
    assert logger.name == "app.AI_agents.test"
    
    with pytest.raises(AIAgentException):
        raise AIAgentException("AIAgentError")

from app.AI_agents.knowledge import RAGPipeline, MedicalRetriever, DocumentLoader, TextSplitter

def test_knowledge_imports():
    assert RAGPipeline is not None
    assert MedicalRetriever is not None
    assert DocumentLoader is not None
    assert TextSplitter is not None

from app.AI_agents.memory import MemoryManager, get_embeddings, create_in_memory_vector_store
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

def test_memory_utilities():
    # Test MemoryManager pruning
    manager = MemoryManager()
    sys_msg = SystemMessage(content="system instructions")
    messages = [sys_msg] + [HumanMessage(content=f"msg {i}") for i in range(20)]
    
    pruned = manager.prune_messages(messages, limit=5)
    assert len(pruned) == 6 # 1 system message + 5 pruned active messages
    assert pruned[0] == sys_msg
    assert pruned[-1].content == "msg 19"

    # Test embeddings & vector store
    embeddings = get_embeddings()
    assert embeddings is not None
    
    store = create_in_memory_vector_store()
    assert store is not None

from app.AI_agents.models import AgentCallbackHandler

def test_callback_handler():
    handler = AgentCallbackHandler()
    assert handler is not None
    
    # Trigger log methods to ensure no exceptions are raised
    handler.on_llm_start({}, ["test prompt"])
    handler.on_llm_end({})
    handler.on_llm_error(ValueError("test error"))

from app.AI_agents.orchestrator.agent_orchestrator import AgentOrchestrator

@pytest.mark.anyio
async def test_agent_orchestrator():
    with patch("app.AI_agents.orchestrator.state_manager.FirestoreCheckpointer") as mock_cp:
        mock_cp_instance = MagicMock()
        mock_cp.return_value = mock_cp_instance
        
        with patch("app.AI_agents.workflows.router_graph.RouterGraph.compile") as mock_compile:
            mock_chain = MagicMock()
            mock_compile.return_value = mock_chain
            mock_chain.ainvoke = AsyncMock(return_value={"messages": [AIMessage(content="Orchestrated response")]})

            orchestrator = AgentOrchestrator()
            res = await orchestrator.run_agent("Hello", "thread-1")
            assert res["messages"][-1].content == "Orchestrated response"

from app.AI_agents.tools import tool_registry

def test_tool_registry():
    assert tool_registry is not None
    assert "baby_profile_tool" in tool_registry.list_tools()
    tool = tool_registry.get_tool("baby_profile_tool")
    assert tool.name == "baby_profile_tool"
    
    with pytest.raises(ValueError):
        tool_registry.get_tool("invalid_tool")

from app.AI_agents.utils import calculate_baby_age, format_agent_response, sanitize_baby_id
from app.AI_agents.utils import validate_baby_id, validate_audio_file, validate_message_not_empty

def test_utils():
    # Helpers
    age = calculate_baby_age("2025-01-01")
    assert "display" in age
    assert age["days"] > 0
    
    resp = format_agent_response("OK", next_step="chat")
    assert resp["response"] == "OK"
    assert resp["next_step"] == "chat"
    
    assert sanitize_baby_id("  baby-1  ") == "baby-1"
    assert sanitize_baby_id("") is None
    assert sanitize_baby_id(None) is None
    
    # Validators
    assert validate_baby_id("baby-123")
    assert not validate_baby_id("")
    assert not validate_baby_id(None)
    
    assert validate_audio_file("cry.wav")
    assert validate_audio_file("audio.mp3")
    assert not validate_audio_file("image.jpg")
    assert not validate_audio_file(None)
    
    assert validate_message_not_empty("hello")
    assert not validate_message_not_empty("")
    assert not validate_message_not_empty(None)


from app.ai.speech_to_text.transcriber import SpeechTranscriber
from unittest.mock import mock_open

def test_speech_transcriber_text_passthrough():
    transcriber = SpeechTranscriber()
    assert transcriber.transcribe_text("  hello  ") == "hello"


def test_speech_transcriber_file_not_found():
    transcriber = SpeechTranscriber()
    assert transcriber.transcribe("non_existent_file.wav") is None


@pytest.mark.anyio
async def test_speech_transcriber_whisper_mode():
    transcriber = SpeechTranscriber()
    transcriber.provider = "whisper"
    
    with patch("app.ai.speech_to_text.transcriber.settings") as mock_settings:
        mock_settings.STT_PROVIDER = "whisper"
        mock_settings.WHISPER_MODEL_SIZE = "tiny"
        mock_settings.WHISPER_MODEL_DIR = "app/ai/models/faster-whisper"
        
        def mock_isfile(path):
            return path == "dummy.wav"
            
        with patch("app.ai.speech_to_text.transcriber.os.path.isfile", side_effect=mock_isfile):
            with patch("faster_whisper.WhisperModel") as mock_whisper_class:
                mock_model = MagicMock()
                mock_whisper_class.return_value = mock_model
                
                mock_segment = MagicMock()
                mock_segment.text = "Hello baby"
                mock_model.transcribe.return_value = ([mock_segment], MagicMock())
                
                result = transcriber.transcribe("dummy.wav")
                assert result == "Hello baby"
                mock_whisper_class.assert_called_once_with(
                    "tiny",
                    device="cpu",
                    compute_type="float32",
                    download_root="app/ai/models/faster-whisper"
                )


@pytest.mark.anyio
async def test_speech_transcriber_whisper_fallback_to_gemini():
    transcriber = SpeechTranscriber()
    transcriber.provider = "whisper"
    
    with patch("app.ai.speech_to_text.transcriber.settings") as mock_settings:
        mock_settings.STT_PROVIDER = "whisper"
        mock_settings.WHISPER_MODEL_SIZE = "tiny"
        mock_settings.WHISPER_MODEL_DIR = "app/ai/models/faster-whisper"
        mock_settings.GEMINI_API_KEY = "dummy-key"
        
        def mock_isfile(path):
            return path == "dummy.wav"
            
        with patch("app.ai.speech_to_text.transcriber.os.path.isfile", side_effect=mock_isfile):
            with patch("faster_whisper.WhisperModel") as mock_whisper_class:
                mock_whisper_class.side_effect = Exception("CUDA error")
                
                import google.generativeai
                with patch("google.generativeai.GenerativeModel") as mock_gen_model_class:
                    mock_model = MagicMock()
                    mock_gen_model_class.return_value = mock_model
                    mock_response = MagicMock()
                    mock_response.text = "Gemini response text"
                    mock_model.generate_content.return_value = mock_response
                    
                    with patch("builtins.open", mock_open(read_data=b"dummy audio data")):
                        result = transcriber.transcribe("dummy.wav")
                        assert result == "Gemini response text"

