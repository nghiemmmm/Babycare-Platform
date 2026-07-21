class AIAgentException(Exception):
    """Base exception for all AI agent framework errors."""
    pass

class LLMConnectionError(AIAgentException):
    """Raised when the LLM service connection fails."""
    pass

class IntentClassificationError(AIAgentException):
    """Raised when the intent planner fails to classify user query."""
    pass

class RAGRetrievalError(AIAgentException):
    """Raised when medical retriever encounters problems."""
    pass
