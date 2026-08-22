from typing import List, Optional
from langchain_core.messages import AnyMessage, SystemMessage, HumanMessage, AIMessage

class MemoryManager:
    """
    Manages agent conversation logs, history, token-aware selection, and context injection.
    """
    def __init__(self, max_tokens: int = 4000):
        self.max_tokens = max_tokens

    def select_messages_by_token_budget(
        self,
        messages: List[AnyMessage],
        max_history_tokens: int = 2000,
        fallback_limit: int = 15
    ) -> List[AnyMessage]:
        """
        Lựa chọn danh sách tin nhắn dựa trên Token Budget:
        1. Luôn giữ nguyên tất cả SystemMessage.
        2. Duyệt lịch sử từ tin nhắn mới nhất ngược về quá khứ.
        3. Tích lũy tin nhắn miễn là tổng token <= max_history_tokens.
        4. Giữ nguyên thứ tự thời gian (chronological order) của tin nhắn.
        """
        if not messages:
            return []

        from app.AI_agents.context.token_budget import TokenBudget

        system_msgs = [m for m in messages if isinstance(m, SystemMessage)]
        other_msgs = [m for m in messages if not isinstance(m, SystemMessage)]

        if not other_msgs:
            return system_msgs

        selected_others: List[AnyMessage] = []
        accumulated_tokens = 0

        # Duyệt từ tin nhắn mới nhất ngược về quá khứ
        for msg in reversed(other_msgs):
            msg_tokens = TokenBudget.estimate_message_tokens(msg)
            if accumulated_tokens + msg_tokens <= max_history_tokens or not selected_others:
                selected_others.append(msg)
                accumulated_tokens += msg_tokens
            else:
                break

        # Khôi phục thứ tự thời gian ban đầu
        selected_others.reverse()
        return system_msgs + selected_others

    def prune_messages(self, messages: list[AnyMessage], limit: int = 15, max_tokens: Optional[int] = None) -> list[AnyMessage]:
        """
        Hàm tương thích ngược: Sử dụng select_messages_by_token_budget nếu max_tokens được truyền,
        hoặc fallback về limit count.
        """
        if max_tokens is not None:
            return self.select_messages_by_token_budget(messages, max_history_tokens=max_tokens, fallback_limit=limit)

        if len(messages) <= limit:
            return messages

        system_msgs = [m for m in messages if isinstance(m, SystemMessage)]
        other_msgs = [m for m in messages if not isinstance(m, SystemMessage)]
        
        pruned_others = other_msgs[-limit:]
        return system_msgs + pruned_others

    async def summarize_old_messages(
        self,
        dropped_messages: List[AnyMessage],
        existing_summary: Optional[str] = None
    ) -> str:
        """
        Tóm tắt các tin nhắn cũ bị vượt quá Token Budget:
        - Chỉ kích hoạt khi dropped_messages >= 3.
        - Trích xuất thông tin quan trọng: chủ đề chính, ý định của phụ huynh, thông tin sức khỏe/dinh dưỡng, quyết định đã đưa ra.
        """
        if not dropped_messages or len(dropped_messages) < 3:
            return existing_summary or ""

        try:
            from app.AI_agents.core.reasoner import AIReasoner
            reasoner = AIReasoner()

            prompt = (
                "Hãy tóm tắt ngắn gọn các tin nhắn hội thoại cũ dưới đây thành 1 đoạn tổng quan (dưới 150 từ).\n"
                "Tóm tắt phải bảo toàn các thông tin cốt lõi:\n"
                "1. Chủ đề chính và ý định nuôi dạy con của phụ huynh\n"
                "2. Các thông tin sức khỏe, dinh dưỡng hoặc chỉ số của bé đã được nhắc tới\n"
                "3. Các quyết định hoặc lời khuyên quan trọng đã được đồng ý\n"
            )
            if existing_summary:
                prompt += f"\n\n# TÓM TẮT TRƯỚC ĐÓ:\n{existing_summary}\n\nHãy bổ sung thêm diễn biến mới từ các tin nhắn dưới đây:"

            new_summary = await reasoner.areason_with_history(
                messages=dropped_messages,
                system_instruction=prompt
            )
            return new_summary.strip()
        except Exception as e:
            return existing_summary or ""

