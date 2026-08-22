import os
import numpy as np
from typing import List
from langchain_core.embeddings import Embeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from app.core.config import settings

# Path đến model BGE-M3 đã download về local
_BGE_M3_LOCAL_PATH = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "..", "..", "ai", "models",
    "models--BAAI--bge-m3", "snapshots",
    "5617a9f61b028005a4858fdac845db406aefb181"
))

# Singleton — chỉ load 1 lần vào RAM
_bge_model = None


def _get_bge_model():
    """Lazy-load BGE-M3 model singleton. Thread-safe đủ dùng với uvicorn single-worker."""
    global _bge_model
    if _bge_model is None:
        try:
            import torch
            torch.set_num_threads(1)
        except Exception:
            pass
        from sentence_transformers import SentenceTransformer
        _bge_model = SentenceTransformer(
            _BGE_M3_LOCAL_PATH,
            device="cpu",
            local_files_only=True
        )
    return _bge_model




class LocalBGEM3Embeddings(Embeddings):
    """
    LangChain-compatible embedding class dùng BGE-M3 local.
    - Không cần internet / API key
    - Dimension: 1024
    - Hỗ trợ tiếng Việt tốt
    - Model load 1 lần, dùng chung mọi request (singleton)
    """

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        import torch
        model = _get_bge_model()
        with torch.inference_mode():
            vectors = model.encode(
                texts,
                normalize_embeddings=True,   # cosine similarity = dot product sau khi normalize
                show_progress_bar=False,
                batch_size=32,
            )
        return vectors.tolist()

    def embed_query(self, text: str) -> List[float]:
        import torch
        model = _get_bge_model()
        with torch.inference_mode():
            vector = model.encode(
                text,
                normalize_embeddings=True,
                show_progress_bar=False,
            )
        return vector.tolist()



class FakeEmbeddings(Embeddings):
    """Test double for Embeddings - dùng trong unit test để mock get_embeddings(), tránh
    gọi model thật (cần RAM và thời gian load)."""
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [[1.0] * 1024 for _ in texts]
    def embed_query(self, text: str) -> List[float]:
        return [1.0] * 1024


def get_embeddings() -> LocalBGEM3Embeddings:
    """
    Trả về embedding model mặc định — BGE-M3 local (BAAI/bge-m3).
    Không tốn API quota. Model load lazy lần đầu gọi, sau đó reuse singleton.
    """
    return LocalBGEM3Embeddings()


def get_gemini_embeddings() -> GoogleGenerativeAIEmbeddings:
    """Fallback: Gemini cloud embedding. Dùng khi BGE-M3 không khả dụng."""
    return GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        google_api_key=settings.GEMINI_API_KEY,
        output_dimensionality=768,
    )

