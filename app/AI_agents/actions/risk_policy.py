"""
Action Risk Policy Module
=========================
Evaluates safety and risk levels for BabyCare Actions:
- Medication is HIGH RISK (requires parent confirmation).
- Feeding, Sleep, Diaper are LOW RISK (safe for direct auto-execution).
"""
from typing import Tuple
from app.AI_agents.actions.schemas import ActionType, ActionRiskLevel, BabyCareAction


class ActionRiskPolicy:
    """
    Chốt chặn an toàn y tế và chính sách Human-in-the-Loop cho các Action.
    """

    @classmethod
    def evaluate(cls, action: BabyCareAction) -> Tuple[ActionRiskLevel, bool]:
        """
        Đánh giá mức độ rủi ro và cờ requires_confirmation.
        Returns:
            Tuple (ActionRiskLevel, requires_confirmation)
        """
        # 1. Thuốc và Vitamin: Bắt buộc xác nhận an toàn
        if action.action_type == ActionType.CREATE_MEDICATION:
            return ActionRiskLevel.HIGH, True

        # 2. Cữ ăn / Dinh dưỡng: Kiểm tra cảnh báo định lượng
        if action.action_type == ActionType.CREATE_FEEDING:
            amount = action.parameters.get("amount", 0.0)
            if amount > 400.0:  # Lượng sữa quá lớn so với dung tích dạ dày của bé
                return ActionRiskLevel.HIGH, True
            return ActionRiskLevel.LOW, False

        # 3. Giấc ngủ và Tã bỉm: Rủi ro thấp, tự động thực thi
        return ActionRiskLevel.LOW, False
