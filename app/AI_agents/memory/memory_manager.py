from langchain_core.messages import AnyMessage, SystemMessage, HumanMessage, AIMessage

class MemoryManager:
    """
    Manages agent conversation logs, history, pruning, and context injection.
    """
    def __init__(self, max_tokens: int = 4000):
        self.max_tokens = max_tokens

    def prune_messages(self, messages: list[AnyMessage], limit: int = 15) -> list[AnyMessage]:
        """
        Trims older messages to keep the context size within limits.
        Always preserves the first system message if present.
        """
        if len(messages) <= limit:
            return messages

        system_msgs = [m for m in messages if isinstance(m, SystemMessage)]
        other_msgs = [m for m in messages if not isinstance(m, SystemMessage)]
        
        pruned_others = other_msgs[-limit:]
        return system_msgs + pruned_others
