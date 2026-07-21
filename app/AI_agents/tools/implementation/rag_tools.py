"""
GraphRAG Knowledge Tools Module

Declares tools to search and retrieve from the medical knowledge database.
"""
from app.AI_agents.tools.base_tool import BaseTool
from app.AI_agents.knowledge.retriever import MedicalRetriever

class KnowledgeRetrievalTool(BaseTool):
    name = "knowledge_retrieval_tool"
    description = "Query GraphRAG database for verified medical parenting guidelines."

    def _run(self, query: str):
        retriever = MedicalRetriever()
        return retriever.retrieve_context(query)
