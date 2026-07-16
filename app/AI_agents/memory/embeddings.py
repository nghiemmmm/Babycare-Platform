from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_core.embeddings import Embeddings
from app.core.config import settings

class FakeEmbeddings(Embeddings):
    """Fallback embedding class for offline/testing mode when no API key is set."""
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [[1.0] * 768 for _ in texts]
    def embed_query(self, text: str) -> list[float]:
        return [1.0] * 768

def get_embeddings() -> Embeddings:
    if settings.GEMINI_API_KEY:
        return GoogleGenerativeAIEmbeddings(
            model="models/text-embedding-004",
            google_api_key=settings.GEMINI_API_KEY
        )
    return FakeEmbeddings()
