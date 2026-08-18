from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from langchain_core.messages import AnyMessage

class ContextSource(str, Enum):
    SYSTEM_INSTRUCTION = "system_instruction"
    BABY_PROFILE = "baby_profile"
    DB_FACTS = "db_facts"
    RECENT_MESSAGES = "recent_messages"
    CONVERSATION_SUMMARY = "conversation_summary"
    RAG_DOCS = "rag_docs"
    LONG_TERM_MEMORY = "long_term_memory"

@dataclass
class ContextItem:
    source: ContextSource
    content: str
    priority: int = 50  # 1-100, higher = higher priority
    token_count: int = 0
    relevance_score: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ContextBundle:
    system_instruction: str
    messages: List[AnyMessage] = field(default_factory=list)
    rag_context: str = ""
    long_term_facts: str = ""
    conversation_summary: str = ""
    total_tokens: int = 0
    token_breakdown: Dict[str, int] = field(default_factory=dict)
    sources_included: List[ContextSource] = field(default_factory=list)
    tool_steps: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "system_instruction": self.system_instruction,
            "message_count": len(self.messages),
            "rag_context": self.rag_context,
            "long_term_facts": self.long_term_facts,
            "conversation_summary": self.conversation_summary,
            "total_tokens": self.total_tokens,
            "token_breakdown": self.token_breakdown,
            "sources_included": [s.value for s in self.sources_included],
            "tool_steps": self.tool_steps
        }
