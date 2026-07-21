import os
from app.AI_agents.knowledge.document_loader import DocumentLoader
from app.AI_agents.knowledge.text_splitter import TextSplitter
from langchain_community.vectorstores import FAISS
from app.AI_agents.memory.embeddings import get_embeddings
from app.AI_agents.core.constant import FAISS_INDEX_DIR, HYBRID_RETRIEVE_CANDIDATES
from app.AI_agents.knowledge.sparse_retriever import SparseBM25Retriever

class RAGPipeline:
    def __init__(self):
        self.loader = DocumentLoader()
        self.splitter = TextSplitter()
        self.embeddings = get_embeddings()
        self.vector_store = None
        self.sparse_retriever = SparseBM25Retriever()
        self.reranker = None  # Lazy init to save startup memory/time
        self._initialize_pipeline()

    def _initialize_pipeline(self):
        """Load documents, split them, and index them in the FAISS vector store. Save/load locally to avoid rebuilding."""
        index_dir = FAISS_INDEX_DIR
        
        if os.path.exists(index_dir):
            try:
                self.vector_store = FAISS.load_local(
                    folder_path=index_dir,
                    embeddings=self.embeddings,
                    allow_dangerous_deserialization=True
                )
            except Exception as e:
                print(f"Không thể tải FAISS index cục bộ, tiến hành dựng lại: {e}")

        # Always parse and split documents to fit the BM25 sparse retriever
        docs = self.loader.load()
        chunks = self.splitter.split_documents(docs)
        
        if chunks:
            self.sparse_retriever.fit(chunks)
            if not self.vector_store:
                self.vector_store = FAISS.from_documents(chunks, self.embeddings)
                try:
                    self.vector_store.save_local(index_dir)
                except Exception as e:
                    print(f"Lỗi khi lưu FAISS index cục bộ: {e}")
        else:
            # FAISS requires at least one document to initialize
            from langchain_core.documents import Document
            dummy_doc = Document(page_content="dummy", metadata={"source": "dummy"})
            self.sparse_retriever.fit([dummy_doc])
            if not self.vector_store:
                self.vector_store = FAISS.from_documents([dummy_doc], self.embeddings)

    def retrieve(self, query: str, k: int = 3, metadata_filter: dict = None) -> list:
        """Retrieve relevant document chunks for the query using Hybrid Retrieval + Reranking."""
        if not self.vector_store:
            return []
            
        filter_func = None
        if metadata_filter:
            def metadata_filter_func(metadata: dict) -> bool:
                if "category" in metadata_filter and metadata.get("category") != metadata_filter["category"]:
                    return False
                if "baby_age" in metadata_filter and metadata_filter["baby_age"] is not None:
                    try:
                        age = int(metadata_filter["baby_age"])
                        min_age = int(metadata.get("age_min_months", 0))
                        max_age = int(metadata.get("age_max_months", 999))
                        if not (min_age <= age <= max_age):
                            return False
                    except (ValueError, TypeError):
                        pass
                return True
            filter_func = metadata_filter_func
            
        try:
            # 1. Retrieve candidates from Dense (FAISS)
            dense_k = HYBRID_RETRIEVE_CANDIDATES
            dense_docs = self.vector_store.similarity_search(query, k=dense_k, filter=filter_func)
        except Exception:
            dense_docs = []
            
        try:
            # 2. Retrieve candidates from Sparse (BM25)
            sparse_k = HYBRID_RETRIEVE_CANDIDATES
            sparse_docs = self.sparse_retriever.retrieve(query, k=sparse_k, filter_func=filter_func)
        except Exception:
            sparse_docs = []
            
        # 3. Merge candidates and remove duplicates (comparing page_content)
        seen = set()
        merged_candidates = []
        for doc in dense_docs + sparse_docs:
            content = doc.page_content.strip()
            if content not in seen:
                seen.add(content)
                merged_candidates.append(doc)
                
        if not merged_candidates:
            return []
            
        # 4. Local Reranker
        if self.reranker is None:
            from app.AI_agents.knowledge.reranker import LocalReranker
            self.reranker = LocalReranker()
            
        try:
            reranked_docs = self.reranker.rerank(query, merged_candidates, top_k=k)
            return reranked_docs
        except Exception as e:
            # Fallback to dense docs if reranker fails
            print(f"Reranking failed: {e}")
            return dense_docs[:k]
