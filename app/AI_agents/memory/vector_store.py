from langchain_core.vectorstores import InMemoryVectorStore
from app.AI_agents.memory.embeddings import get_embeddings

def create_in_memory_vector_store() -> InMemoryVectorStore:
    """Creates an instanced in-memory vector store with fallback embeddings."""
    embeddings = get_embeddings()
    return InMemoryVectorStore(embeddings)
