from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.embeddings import Embeddings

class FakeEmbeddings(Embeddings):
    """Fallback embedding class for offline/testing mode when no API key is set."""
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [[1.0] * 1024 for _ in texts]
    def embed_query(self, text: str) -> list[float]:
        return [1.0] * 1024

def get_embeddings() -> Embeddings:
    return HuggingFaceEmbeddings(
        model_name="BAAI/bge-m3",
        model_kwargs={"device": "cpu"},
        cache_folder="app/ai/models"
    )

