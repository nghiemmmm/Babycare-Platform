import os
from app.core.config import settings

class AIAgentConfig:
    DEFAULT_TEMPERATURE: float = 0.0
    DEFAULT_CHAT_MODEL: str = "gemini-2.5-flash"
    COMPLEX_REASONING_MODEL: str = "gemini-1.5-pro"
    
    # RAG Settings
    RAG_CHUNK_SIZE: int = 500
    RAG_CHUNK_OVERLAP: int = 50
    RAG_DOCUMENT_DIR: str = "app/AI_agents/knowledge/documents"
    
    # Firestore Settings
    CHECKPOINT_COLLECTION: str = "chat_checkpoints"

agent_config = AIAgentConfig()
