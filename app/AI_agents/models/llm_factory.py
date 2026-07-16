from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.config import settings

class LLMFactory:
    @staticmethod
    def get_model(model_name: str = "gemini-1.5-flash", temperature: float = 0.0) -> ChatGoogleGenerativeAI:
        """
        Factory method to instantiate configured LLM models.
        """
        if model_name.startswith("gemini"):
            return ChatGoogleGenerativeAI(
                model=model_name,
                google_api_key=settings.GEMINI_API_KEY,
                temperature=temperature
            )
        else:
            # Fallback to default gemini model
            return ChatGoogleGenerativeAI(
                model="gemini-1.5-flash",
                google_api_key=settings.GEMINI_API_KEY,
                temperature=temperature
            )
