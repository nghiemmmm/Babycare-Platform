import logging
from typing import List, Dict, Any, Optional
from langchain_core.messages import AnyMessage, SystemMessage, HumanMessage, AIMessage

from app.AI_agents.context.context_types import ContextItem, ContextSource, ContextBundle
from app.AI_agents.context.token_budget import TokenBudget
from app.AI_agents.memory.memory_manager import MemoryManager

logger = logging.getLogger(__name__)

class ContextBuilder:
    """
    Centralized Context Engineering Manager cho BabyCare AI.
    Thu thập, phân loại nguồn, loại bỏ trùng lặp, áp dụng thứ tự ưu tiên (Priority)
    và kiểm soát Global Token Budget trước khi đưa sang LLM.
    """
    def __init__(self, memory_manager: Optional[MemoryManager] = None):
        self.memory_manager = memory_manager or MemoryManager()

    @staticmethod
    def build_chat_context(
        system_template: str,
        baby_profile_data: Dict[str, Any],
        rag_context: str,
        messages: List[AnyMessage],
        conversation_summary: Optional[str] = None,
        long_term_facts: Optional[str] = None,
        tool_steps: Optional[List[Dict[str, Any]]] = None,
        max_budget: int = 4000
    ) -> ContextBundle:
        """
        Build standardized ContextBundle cho Chat Agent.
        """
        items: List[ContextItem] = []
        token_breakdown: Dict[str, int] = {}
        sources_included: List[ContextSource] = []

        # 1. System Persona & Core Instructions (Priority 100 - Highest)
        baby_name = baby_profile_data.get("baby_name", "Bé")
        baby_gender = baby_profile_data.get("baby_gender", "chưa rõ")
        baby_age = baby_profile_data.get("baby_age", "chưa rõ")
        baby_birth_date = baby_profile_data.get("baby_birth_date", "chưa rõ")
        growth_info = baby_profile_data.get("growth_info", "chưa có dữ liệu")

        sys_prompt = system_template.format(
            baby_name=baby_name,
            baby_gender=baby_gender,
            baby_age=baby_age,
            baby_birth_date=baby_birth_date,
            growth_info=growth_info
        )
        sys_tokens = TokenBudget.estimate_tokens(sys_prompt)
        token_breakdown["system_instruction"] = sys_tokens
        sources_included.append(ContextSource.SYSTEM_INSTRUCTION)

        # 1b. Long-Term Memory Facts (Priority 85)
        if long_term_facts and long_term_facts.strip():
            lt_tokens = TokenBudget.estimate_tokens(long_term_facts)
            token_breakdown["long_term_memory"] = lt_tokens
            sources_included.append(ContextSource.LONG_TERM_MEMORY)
            sys_prompt += f"\n\n# DỮ LIỆU BỀN VỮNG VỀ BÉ (LONG-TERM FACTS):\n{long_term_facts}"

        # 1c. Conversation Summary Buffer (Priority 60)
        if conversation_summary and conversation_summary.strip():
            sum_tokens = TokenBudget.estimate_tokens(conversation_summary)
            token_breakdown["conversation_summary"] = sum_tokens
            sources_included.append(ContextSource.CONVERSATION_SUMMARY)
            sys_prompt += f"\n\n# TÓM TẮT DIỄN BIẾN HỘI THOẠI TRƯỚC ĐÓ:\n{conversation_summary}"

        # 2. RAG WHO Reference Docs (Priority 70)
        final_rag_context = ""
        rag_tokens = 0
        if rag_context and rag_context.strip():
            rag_tokens = TokenBudget.estimate_tokens(rag_context)
            if rag_tokens > TokenBudget.RAG_MAX_TOKENS:
                words = rag_context.split()
                max_words = int(TokenBudget.RAG_MAX_TOKENS / 1.3)
                rag_context = " ".join(words[:max_words]) + "..."
                rag_tokens = TokenBudget.RAG_MAX_TOKENS

            final_rag_context = rag_context
            token_breakdown["rag_docs"] = rag_tokens
            sources_included.append(ContextSource.RAG_DOCS)

            rag_instruction = f"\n\n# TÀI LIỆU THAM CHIẾU RAG WHO:\n{final_rag_context}\n\n*YÊU CẦU TRÍCH DẪN: Ở cuối câu trả lời, hãy đính kèm rõ ràng một dòng: '--- Nguồn tham khảo: Tài liệu mốc phát triển & chăm sóc trẻ em chuẩn WHO'.*"
            sys_prompt += rag_instruction

        # 3. Conversation Messages (Priority 50 - Token Budgeted dynamically)
        memory_mgr = MemoryManager()
        used_tokens = sys_tokens + rag_tokens + token_breakdown.get("conversation_summary", 0) + token_breakdown.get("long_term_memory", 0)
        history_budget = max(max_budget - used_tokens, 1000)
        pruned_msgs = memory_mgr.select_messages_by_token_budget(messages or [], max_history_tokens=history_budget)
        history_tokens = sum(TokenBudget.estimate_message_tokens(m) for m in pruned_msgs)
        token_breakdown["recent_messages"] = history_tokens
        sources_included.append(ContextSource.RECENT_MESSAGES)

        total_tokens = sum(token_breakdown.values())

        return ContextBundle(
            system_instruction=sys_prompt,
            messages=pruned_msgs,
            rag_context=final_rag_context,
            long_term_facts=long_term_facts or "",
            conversation_summary=conversation_summary or "",
            total_tokens=total_tokens,
            token_breakdown=token_breakdown,
            sources_included=sources_included,
            tool_steps=tool_steps or []
        )

    @staticmethod
    def build_health_context(
        base_prompt: str,
        health_records_context: str,
        rag_context: str,
        messages: List[AnyMessage],
        conversation_summary: Optional[str] = None,
        long_term_facts: Optional[str] = None,
        tool_steps: Optional[List[Dict[str, Any]]] = None,
        max_budget: int = 4000
    ) -> ContextBundle:
        """
        Build standardized ContextBundle cho Health Agent.
        """
        token_breakdown: Dict[str, int] = {}
        sources_included: List[ContextSource] = []

        sys_prompt = f"{base_prompt}\n\n{health_records_context}"
        sys_tokens = TokenBudget.estimate_tokens(sys_prompt)
        token_breakdown["system_instruction"] = sys_tokens
        sources_included.append(ContextSource.SYSTEM_INSTRUCTION)
        if health_records_context:
            sources_included.append(ContextSource.DB_FACTS)

        if long_term_facts and long_term_facts.strip():
            lt_tokens = TokenBudget.estimate_tokens(long_term_facts)
            token_breakdown["long_term_memory"] = lt_tokens
            sources_included.append(ContextSource.LONG_TERM_MEMORY)
            sys_prompt += f"\n\n# DỮ LIỆU BỀN VỮNG VỀ BÉ (LONG-TERM FACTS):\n{long_term_facts}"

        if conversation_summary and conversation_summary.strip():
            sum_tokens = TokenBudget.estimate_tokens(conversation_summary)
            token_breakdown["conversation_summary"] = sum_tokens
            sources_included.append(ContextSource.CONVERSATION_SUMMARY)
            sys_prompt += f"\n\n# TÓM TẮT DIỄN BIẾN HỘI THOẠI TRƯỚC ĐÓ:\n{conversation_summary}"

        final_rag_context = ""
        rag_tokens = 0
        if rag_context and rag_context.strip():
            rag_tokens = TokenBudget.estimate_tokens(rag_context)
            if rag_tokens > TokenBudget.RAG_MAX_TOKENS:
                words = rag_context.split()
                max_words = int(TokenBudget.RAG_MAX_TOKENS / 1.3)
                rag_context = " ".join(words[:max_words]) + "..."
                rag_tokens = TokenBudget.RAG_MAX_TOKENS
            final_rag_context = rag_context
            token_breakdown["rag_docs"] = rag_tokens
            sources_included.append(ContextSource.RAG_DOCS)

            sys_prompt += f"\n\nTài liệu y khoa tham chiếu:\n{final_rag_context}"

        memory_mgr = MemoryManager()
        used_tokens = sys_tokens + rag_tokens + token_breakdown.get("conversation_summary", 0) + token_breakdown.get("long_term_memory", 0)
        history_budget = max(max_budget - used_tokens, 1000)
        pruned_msgs = memory_mgr.select_messages_by_token_budget(messages or [], max_history_tokens=history_budget)
        history_tokens = sum(TokenBudget.estimate_message_tokens(m) for m in pruned_msgs)
        token_breakdown["recent_messages"] = history_tokens
        sources_included.append(ContextSource.RECENT_MESSAGES)

        total_tokens = sum(token_breakdown.values())

        return ContextBundle(
            system_instruction=sys_prompt,
            messages=pruned_msgs,
            rag_context=final_rag_context,
            long_term_facts=long_term_facts or "",
            conversation_summary=conversation_summary or "",
            total_tokens=total_tokens,
            token_breakdown=token_breakdown,
            sources_included=sources_included,
            tool_steps=tool_steps or []
        )

    @staticmethod
    def build_nutrition_context(
        base_prompt: str,
        nutrition_context: str,
        growth_context: str,
        rag_context: str,
        messages: List[AnyMessage],
        conversation_summary: Optional[str] = None,
        long_term_facts: Optional[str] = None,
        tool_steps: Optional[List[Dict[str, Any]]] = None,
        max_budget: int = 4000
    ) -> ContextBundle:
        """
        Build standardized ContextBundle cho Nutrition Agent.
        """
        token_breakdown: Dict[str, int] = {}
        sources_included: List[ContextSource] = []

        sys_prompt = f"{base_prompt}\n\n{nutrition_context}\n\n{growth_context}"
        sys_tokens = TokenBudget.estimate_tokens(sys_prompt)
        token_breakdown["system_instruction"] = sys_tokens
        sources_included.append(ContextSource.SYSTEM_INSTRUCTION)
        if nutrition_context or growth_context:
            sources_included.append(ContextSource.DB_FACTS)

        if long_term_facts and long_term_facts.strip():
            lt_tokens = TokenBudget.estimate_tokens(long_term_facts)
            token_breakdown["long_term_memory"] = lt_tokens
            sources_included.append(ContextSource.LONG_TERM_MEMORY)
            sys_prompt += f"\n\n# DỮ LIỆU BỀN VỮNG VỀ BÉ (LONG-TERM FACTS):\n{long_term_facts}"

        if conversation_summary and conversation_summary.strip():
            sum_tokens = TokenBudget.estimate_tokens(conversation_summary)
            token_breakdown["conversation_summary"] = sum_tokens
            sources_included.append(ContextSource.CONVERSATION_SUMMARY)
            sys_prompt += f"\n\n# TÓM TẮT DIỄN BIẾN HỘI THOẠI TRƯỚC ĐÓ:\n{conversation_summary}"

        final_rag_context = ""
        rag_tokens = 0
        if rag_context and rag_context.strip():
            rag_tokens = TokenBudget.estimate_tokens(rag_context)
            if rag_tokens > TokenBudget.RAG_MAX_TOKENS:
                words = rag_context.split()
                max_words = int(TokenBudget.RAG_MAX_TOKENS / 1.3)
                rag_context = " ".join(words[:max_words]) + "..."
                rag_tokens = TokenBudget.RAG_MAX_TOKENS
            final_rag_context = rag_context
            token_breakdown["rag_docs"] = rag_tokens
            sources_included.append(ContextSource.RAG_DOCS)

            sys_prompt += f"\n\nTài liệu dinh dưỡng tham chiếu:\n{final_rag_context}"

        memory_mgr = MemoryManager()
        used_tokens = sys_tokens + rag_tokens + token_breakdown.get("conversation_summary", 0) + token_breakdown.get("long_term_memory", 0)
        history_budget = max(max_budget - used_tokens, 1000)
        pruned_msgs = memory_mgr.select_messages_by_token_budget(messages or [], max_history_tokens=history_budget)
        history_tokens = sum(TokenBudget.estimate_message_tokens(m) for m in pruned_msgs)
        token_breakdown["recent_messages"] = history_tokens
        sources_included.append(ContextSource.RECENT_MESSAGES)

        total_tokens = sum(token_breakdown.values())

        return ContextBundle(
            system_instruction=sys_prompt,
            messages=pruned_msgs,
            rag_context=final_rag_context,
            long_term_facts=long_term_facts or "",
            conversation_summary=conversation_summary or "",
            total_tokens=total_tokens,
            token_breakdown=token_breakdown,
            sources_included=sources_included,
            tool_steps=tool_steps or []
        )

    @staticmethod
    def build_logging_context(
        extraction_prompt: str,
        messages: List[AnyMessage],
        tool_steps: Optional[List[Dict[str, Any]]] = None,
        max_budget: int = 4000
    ) -> ContextBundle:
        """
        Build standardized ContextBundle cho VoiceLogging Agent.
        """
        token_breakdown: Dict[str, int] = {}
        sources_included: List[ContextSource] = []

        sys_tokens = TokenBudget.estimate_tokens(extraction_prompt)
        token_breakdown["system_instruction"] = sys_tokens
        sources_included.append(ContextSource.SYSTEM_INSTRUCTION)

        memory_mgr = MemoryManager()
        pruned_msgs = memory_mgr.select_messages_by_token_budget(messages or [], max_history_tokens=2000)
        history_tokens = sum(TokenBudget.estimate_message_tokens(m) for m in pruned_msgs)
        token_breakdown["recent_messages"] = history_tokens
        sources_included.append(ContextSource.RECENT_MESSAGES)

        total_tokens = sum(token_breakdown.values())

        return ContextBundle(
            system_instruction=extraction_prompt,
            messages=pruned_msgs,
            rag_context="",
            long_term_facts="",
            conversation_summary="",
            total_tokens=total_tokens,
            token_breakdown=token_breakdown,
            sources_included=sources_included,
            tool_steps=tool_steps or []
        )
