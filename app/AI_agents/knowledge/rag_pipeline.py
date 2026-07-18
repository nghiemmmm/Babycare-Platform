from app.AI_agents.knowledge.document_loader import DocumentLoader
from app.AI_agents.knowledge.text_splitter import TextSplitter
from langchain_community.vectorstores import FAISS
from app.AI_agents.memory.embeddings import get_embeddings

class RAGPipeline:
    def __init__(self):
        self.loader = DocumentLoader()
        self.splitter = TextSplitter()
        self.embeddings = get_embeddings()
        self.vector_store = None
        self._initialize_pipeline()

    def _initialize_pipeline(self):
        """Load documents, split them, and index them in the FAISS vector store. Save/load locally to avoid rebuilding."""
        import os
        index_dir = "app/ai/models/faiss_index"
        
        if os.path.exists(index_dir):
            try:
                self.vector_store = FAISS.load_local(
                    folder_path=index_dir,
                    embeddings=self.embeddings,
                    allow_dangerous_deserialization=True
                )
                return
            except Exception as e:
                print(f"Không thể tải FAISS index cục bộ, tiến hành dựng lại: {e}")

        docs = self.loader.load()
        chunks = self.splitter.split_documents(docs)
        if chunks:
            self.vector_store = FAISS.from_documents(chunks, self.embeddings)
            try:
                self.vector_store.save_local(index_dir)
            except Exception as e:
                print(f"Lỗi khi lưu FAISS index cục bộ: {e}")
        else:
            # FAISS requires at least one document to initialize
            from langchain_core.documents import Document
            dummy_doc = Document(page_content="dummy", metadata={"source": "dummy"})
            self.vector_store = FAISS.from_documents([dummy_doc], self.embeddings)

    def retrieve(self, query: str, k: int = 3) -> list:
        """Retrieve relevant document chunks for the query."""
        if not self.vector_store:
            return []
        try:
            return self.vector_store.similarity_search(query, k=k)
        except Exception:
            return []

