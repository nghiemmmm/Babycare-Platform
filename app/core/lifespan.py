from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from app.infrastructure.database.connection import initialize_firebase

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # ──────────────────────────────────────────────────────────────
    # STARTUP
    # ──────────────────────────────────────────────────────────────
    logger.info("Starting up BabyCare AI application...")

    # 1. Firebase / Firestore
    try:
        initialize_firebase()
        logger.info("[Startup] Firebase initialized.")
    except Exception as e:
        logger.warning(f"[Startup] Firebase initialization warning (non-fatal for basic healthcheck): {e}")

    # 2. BGE-M3 Local Embedding Model — load vào RAM trước khi RAGPipeline dùng
    try:
        from app.AI_agents.memory.embeddings import _get_bge_model
        _get_bge_model()  # trigger load singleton
        logger.info("[Startup] BGE-M3 local embedding model loaded successfully.")
    except Exception as e:
        logger.warning(f"[Startup] BGE-M3 failed to load (non-fatal): {e}")

    # 3. RAGPipeline — load FAISS index từ disk vào RAM & CrossEncoder Reranker
    try:
        from app.AI_agents.knowledge.rag_pipeline import init_rag_pipeline
        from app.AI_agents.knowledge.reranker import _get_cross_encoder
        init_rag_pipeline()
        _get_cross_encoder()  # trigger load CrossEncoder PyTorch weights vào RAM
        logger.info("[Startup] RAGPipeline (FAISS index + CrossEncoder Reranker) loaded successfully.")
    except Exception as e:
        logger.warning(f"[Startup] RAGPipeline failed to load (non-fatal): {e}")

    # 4. AgentOrchestrator — compile tất cả LangGraph agents 1 lần, lưu vào app.state
    try:
        from app.AI_agents.orchestrator.agent_orchestrator import AgentOrchestrator
        app.state.orchestrator = AgentOrchestrator()
        logger.info("[Startup] AgentOrchestrator singleton initialized with all agents registered.")
    except Exception as e:
        logger.warning(f"[Startup] AgentOrchestrator failed to initialize (non-fatal): {e}")
        app.state.orchestrator = None

    # 5. AST PyTorch Model — load cry detection model vào RAM
    try:
        from app.ai.CRY.inference import get_ast_model
        get_ast_model()  # trigger load nếu chưa có
        logger.info("[Startup] AST cry detection model loaded successfully.")
    except Exception as e:
        logger.warning(f"[Startup] AST model failed to load (non-fatal, cry detection will lazy-load): {e}")

    logger.info("BabyCare AI application startup complete.")

    yield  # ← App đang chạy

    # ──────────────────────────────────────────────────────────────
    # SHUTDOWN
    # ──────────────────────────────────────────────────────────────
    logger.info("Shutting down BabyCare AI application...")

    # Giải phóng LLM HTTP connection pools
    try:
        from app.AI_agents.models.llm_factory import LLMFactory
        LLMFactory.clear_cache()
        logger.info("[Shutdown] LLM cache cleared.")
    except Exception as e:
        logger.warning(f"[Shutdown] LLM cache clear failed: {e}")

    # Giải phóng FAISS vector store + BM25 + Reranker khỏi RAM
    try:
        from app.AI_agents.knowledge.rag_pipeline import clear_rag_pipeline
        clear_rag_pipeline()
        logger.info("[Shutdown] RAGPipeline (FAISS + BM25 + Reranker) cleared.")
    except Exception as e:
        logger.warning(f"[Shutdown] RAGPipeline clear failed: {e}")

    # Giải phóng BGE-M3 embedding model khỏi RAM
    try:
        import app.AI_agents.memory.embeddings as emb_module
        emb_module._bge_model = None
        logger.info("[Shutdown] BGE-M3 embedding model cleared.")
    except Exception as e:
        logger.warning(f"[Shutdown] BGE-M3 clear failed: {e}")

    # Giải phóng AST PyTorch model khỏi RAM/VRAM
    try:
        from app.ai.CRY.inference import _ast_singleton
        _ast_singleton.clear()
        logger.info("[Shutdown] AST model cleared from memory.")
    except Exception as e:
        logger.warning(f"[Shutdown] AST model clear failed: {e}")

    logger.info("BabyCare AI application shutdown complete.")


