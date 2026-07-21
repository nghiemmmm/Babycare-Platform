from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from app.AI_agents.core.constant import RAG_CHUNK_SIZE, RAG_CHUNK_OVERLAP

class TextSplitter:
    def __init__(self, chunk_size: int = RAG_CHUNK_SIZE, chunk_overlap: int = RAG_CHUNK_OVERLAP):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len
        )

    def split_documents(self, documents: list[Document]) -> list[Document]:
        return self.splitter.split_documents(documents)
