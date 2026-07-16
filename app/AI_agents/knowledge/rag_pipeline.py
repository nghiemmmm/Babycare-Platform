from app.AI_agents.knowledge.document_loader import DocumentLoader
from app.AI_agents.knowledge.text_splitter import TextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_core.embeddings import Embeddings
from app.core.config import settings

class FakeEmbeddings(Embeddings):
    """Fallback embedding class for offline/testing mode when no API key is set."""
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [[1.0] * 768 for _ in texts]
    def embed_query(self, text: str) -> list[float]:
        return [1.0] * 768

class RAGPipeline:
    def __init__(self):
        self.loader = DocumentLoader()
        self.splitter = TextSplitter()
        
        # Safe fallback initialization
        if settings.GEMINI_API_KEY:
            self.embeddings = GoogleGenerativeAIEmbeddings(
                model="models/text-embedding-004",
                google_api_key=settings.GEMINI_API_KEY
            )
        else:
            self.embeddings = FakeEmbeddings()
            
        self.vector_store = InMemoryVectorStore(self.embeddings)
        self._initialize_pipeline()

    def _initialize_pipeline(self):
        """Load documents, split them, and index them in the in-memory vector store."""
        docs = self.loader.load()
        chunks = self.splitter.split_documents(docs)
        if chunks:
            self.vector_store.add_documents(chunks)

    def retrieve(self, query: str, k: int = 3) -> list:
        """Retrieve relevant document chunks for the query."""
        try:
            return self.vector_store.similarity_search(query, k=k)
        except Exception:
            return []
