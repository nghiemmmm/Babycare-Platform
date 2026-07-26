from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_core.embeddings import Embeddings
from app.core.config import settings


class FakeEmbeddings(Embeddings):
    """Test double for Embeddings - dùng trong unit test để mock get_embeddings(), tránh
    gọi Gemini Embedding API thật (cần network + API key hợp lệ)."""
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [[1.0] * 768 for _ in texts]
    def embed_query(self, text: str) -> list[float]:
        return [1.0] * 768


def get_embeddings() -> GoogleGenerativeAIEmbeddings:
    return GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        google_api_key=settings.GEMINI_API_KEY,
        output_dimensionality=768,
    )

