from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from app.AI_agents.core.config import agent_config

class TextSplitter:
    def __init__(self, chunk_size: int = agent_config.RAG_CHUNK_SIZE, chunk_overlap: int = agent_config.RAG_CHUNK_OVERLAP):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len
        )

    def split_documents(self, documents: list[Document]) -> list[Document]:
        return self.splitter.split_documents(documents)
