"""
Action Dispatcher Module
========================
Multi-Tool Execution Dispatcher for BabyCare:
- Handles Parallel Async Execution via asyncio.gather
- Idempotency & Deduplication
- Partial Failure Management
- Evaluates Risk Gates before execution
"""
import asyncio
import time
import logging
from typing import List, Dict, Set, Optional
from app.AI_agents.actions.schemas import (
    ActionType,
    ActionStatus,
    ActionRiskLevel,
    BabyCareAction,
    ActionResultItem,
    ActionExecutionReport
)
from app.AI_agents.actions.risk_policy import ActionRiskPolicy
from app.AI_agents.actions.consistency import ActionConsistencyValidator
from app.AI_agents.actions.tools import (
    FeedingActionTool,
    SleepActionTool,
    DiaperActionTool,
    MedicationActionTool
)

logger = logging.getLogger(__name__)


class ActionDispatcher:
    """
    Bộ điều phối Multi-Tool Execution song song & an toàn.
    """
    _seen_idempotency_keys: Dict[str, float] = {}

    def __init__(self, consistency_validator: Optional[ActionConsistencyValidator] = None):
        self.tools = {
            ActionType.CREATE_FEEDING: FeedingActionTool(),
            ActionType.CREATE_SLEEP: SleepActionTool(),
            ActionType.CREATE_DIAPER: DiaperActionTool(),
            ActionType.CREATE_MEDICATION: MedicationActionTool(),
        }
        self.consistency_validator = consistency_validator or ActionConsistencyValidator()

    @classmethod
    def _is_duplicate(cls, key: str, window_seconds: int = 60) -> bool:
        """Chống ghi nhận đúp trong khoảng thời gian cửa sổ."""
        now = time.time()
        # Dọn dẹp cache cũ
        cls._seen_idempotency_keys = {k: ts for k, ts in cls._seen_idempotency_keys.items() if now - ts < window_seconds}
        if key in cls._seen_idempotency_keys:
            return True
        cls._seen_idempotency_keys[key] = now
        return False

    async def execute_action(self, action: BabyCareAction, user_id: str) -> ActionResultItem:
        """
        Thực thi một Single Action qua Tool tương ứng.
        """
        tool = self.tools.get(action.action_type)
        if not tool:
            return ActionResultItem(
                action_id=action.action_id,
                action_type=action.action_type,
                status=ActionStatus.FAILED,
                message=f"Không tìm thấy Tool cho hành động: {action.action_type}",
                error="ToolNotFound"
            )

        return await tool.execute(
            action_id=action.action_id,
            baby_id=action.baby_id,
            parameters=action.parameters,
            user_id=user_id
        )

    async def dispatch(self, actions: List[BabyCareAction], user_id: str) -> ActionExecutionReport:
        """
        Điều phối danh sách Actions:
        1. Phân loại Action thiếu trường -> clarifications
        2. Thẩm định tính nhất quán & rủi ro sinh lý -> pending_confirmations / warnings
        3. Thực thi song song các Action hợp lệ còn lại -> executed_actions
        """
        if not actions:
            return ActionExecutionReport(
                success=True,
                summary_message="Không có hành động nào cần thực thi."
            )

        executed_actions: List[ActionResultItem] = []
        pending_confirmations: List[BabyCareAction] = []
        clarifications: List[BabyCareAction] = []
        failed_actions: List[ActionResultItem] = []
        warnings: List[str] = []

        ready_to_execute: List[BabyCareAction] = []

        for act in actions:
            # 1. Kiểm tra thiếu trường dữ liệu bắt buộc
            if act.status == ActionStatus.NEEDS_CLARIFICATION or act.missing_fields:
                act.status = ActionStatus.NEEDS_CLARIFICATION
                clarifications.append(act)
                continue

            # 2. Đánh giá rủi ro an toàn & Xung đột đa người giám hộ
            risk_level, req_confirm = ActionRiskPolicy.evaluate(act)
            act.risk_level = risk_level
            act.requires_confirmation = req_confirm

            # Thẩm định tính nhất quán và cảnh báo an toàn sinh lý
            act, anomaly_warning = await self.consistency_validator.validate_action(act, user_id=user_id)
            if anomaly_warning:
                warnings.append(anomaly_warning)
                if anomaly_warning not in act.warnings:
                    act.warnings.append(anomaly_warning)

            if act.requires_confirmation:
                act.status = ActionStatus.PENDING_CONFIRMATION
                pending_confirmations.append(act)
                continue

            # 3. Kiểm tra trùng lặp Idempotency
            if self._is_duplicate(act.idempotency_key):
                warnings.append(f"Hành động '{act.action_type.value}' vừa được thực thi gần đây. Bỏ qua ghi nhận trùng lặp.")
                continue

            ready_to_execute.append(act)


        # 4. Thực thi song song các Action hợp lệ
        if ready_to_execute:
            tasks = [self.execute_action(act, user_id) for act in ready_to_execute]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for res in results:
                if isinstance(res, Exception):
                    logger.error(f"[ActionDispatcher] Unhandled exception: {res}")
                    failed_actions.append(ActionResultItem(
                        action_id="unknown",
                        action_type=ActionType.CREATE_FEEDING,
                        status=ActionStatus.FAILED,
                        message=f"Lỗi hệ thống: {str(res)}",
                        error=str(res)
                    ))
                elif isinstance(res, ActionResultItem):
                    if res.status == ActionStatus.COMPLETED:
                        executed_actions.append(res)
                    else:
                        failed_actions.append(res)

        # 5. Xây dựng tin nhắn tóm tắt thân thiện
        messages = []
        if executed_actions:
            messages.append("Đã tự động ghi nhận: " + ", ".join([a.message for a in executed_actions]))
        if pending_confirmations:
            messages.append("Cần ba mẹ xác nhận: " + ", ".join([f"Uống {a.parameters.get('medication_name')}" for a in pending_confirmations]))
        if clarifications:
            messages.append("Cần bổ sung thông tin: " + ", ".join([a.clarification_prompt or "vui lòng chọn thêm thông số" for a in clarifications]))

        summary = " | ".join(messages) if messages else "Đã xử lý yêu cầu thành công."

        overall_success = len(failed_actions) == 0 and (len(executed_actions) > 0 or len(pending_confirmations) > 0 or len(clarifications) > 0)

        return ActionExecutionReport(
            success=overall_success,
            executed_actions=executed_actions,
            pending_confirmations=pending_confirmations,
            clarifications=clarifications,
            failed_actions=failed_actions,
            summary_message=summary,
            warnings=warnings
        )
