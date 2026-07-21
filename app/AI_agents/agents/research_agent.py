from app.AI_agents.agents.base_agent import BaseAgent
from app.AI_agents.knowledge.retriever import MedicalRetriever

class ResearchAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="ResearchAgent")
        self.retriever = MedicalRetriever()

    def search(self, query: str) -> str:
        return self.retriever.retrieve_context(query)
