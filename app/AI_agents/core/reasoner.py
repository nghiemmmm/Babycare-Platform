from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from app.core.config import settings

class AIReasoner:
    def __init__(self, model_name: str = "gemini-1.5-flash", temperature: float = 0.0):
        self.model = ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=settings.GEMINI_API_KEY,
            temperature=temperature
        )

    def reason(self, prompt: str, system_instruction: str = None) -> str:
        """Synchronously reason using the model."""
        messages = []
        if system_instruction:
            messages.append(SystemMessage(content=system_instruction))
        messages.append(HumanMessage(content=prompt))
        
        response = self.model.invoke(messages)
        return response.content

    async def areason(self, prompt: str, system_instruction: str = None) -> str:
        """Asynchronously reason using the model."""
        messages = []
        if system_instruction:
            messages.append(SystemMessage(content=system_instruction))
        messages.append(HumanMessage(content=prompt))
        
        response = await self.model.ainvoke(messages)
        return response.content
