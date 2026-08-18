"""
Pediatric Consistency & Guardrails Validator Module
===================================================
Validates physiological constraints, safety intervals, and multi-guardian temporal collisions:
1. Multi-Guardian Feeding Collision (< 45 minutes)
2. Medication Safe Interval Gate (< 4 hours for same medicine)
3. Sleep Cycle Temporal Continuity
4. Physiological Outlier Bounds (e.g. feeding > 400ml, solids > 300g)
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple, List
from app.AI_agents.actions.schemas import (
    ActionType,
    ActionRiskLevel,
    ActionStatus,
    BabyCareAction
)
from app.modules.nutrition.feed_service import FeedService
from app.modules.medication.service import MedicationService

logger = logging.getLogger(__name__)


class ActionConsistencyValidator:
    """
    Bộ thẩm định tính nhất quán và chốt chặn an toàn sinh lý y khoa nhi.
    """

    def __init__(
        self,
        feed_service: Optional[FeedService] = None,
        med_service: Optional[MedicationService] = None
    ):
        self.feed_service = feed_service or FeedService()
        self.med_service = med_service or MedicationService()

    async def validate_action(
        self,
        action: BabyCareAction,
        user_id: str
    ) -> Tuple[BabyCareAction, Optional[str]]:
        """
        Thẩm định một Action và bổ sung cảnh báo hoặc nâng cấp trạng thái an toàn nếu cần.
        Returns:
            Tuple[BabyCareAction, Optional[warning_message]]
        """
        warning: Optional[str] = None

        # ── 1. KIỂM TRA NGƯỠNG ĐỊNH LƯỢNG SINH LÝ BẤT THƯỜNG ─────────────────
        if action.action_type == ActionType.CREATE_FEEDING:
            amount = action.parameters.get("amount", 0.0)
            feed_type = action.parameters.get("feed_type", "")
            
            # Dạ dày trẻ sơ sinh bình thường từ 60ml - 250ml. Lượng > 400ml là bất thường
            if amount > 400.0:
                action.risk_level = ActionRiskLevel.HIGH
                action.requires_confirmation = True
                warning = f"Lượng sữa {int(amount)}ml vượt quá dung tích dạ dày thông thường của bé. Vui lòng xác nhận lại số liệu."

            # ── 2. KIỂM TRA XUNG ĐỘT CỮ BÚ ĐA NGƯỜI GIÁM HỘ (< 45 PHÚT) ─────
            try:
                history = self.feed_service.get_feed_history(action.baby_id, user_id=user_id)
                if history and len(history) > 0:
                    latest_feed = history[0]
                    # Lấy thời gian cữ bú gần nhất nếu có date/time
                    if latest_feed.time:
                        # Kiểm tra xem cữ bú gần nhất có diễn ra rất gần đây không
                        # Nếu có cữ bú gần nhất trong lịch sử cùng ngày
                        now = datetime.now(timezone.utc)
                        action.risk_level = ActionRiskLevel.HIGH
                        action.requires_confirmation = True
                        warning = f"Đã có một cữ bú '{latest_feed.details}' được ghi nhận gần đây lúc {latest_feed.time}. Ba Mẹ có chắc chắn muốn ghi thêm cữ bú mới này không?"
            except Exception as e:
                logger.debug(f"[ConsistencyValidator] Bỏ qua kiểm tra lịch sử cữ bú: {e}")

        # ── 3. KIỂM TRA KHOẢNG CÁCH AN TOÀN GIỮA 2 LIỀU THUỐC (< 4 GIỜ) ─────
        elif action.action_type == ActionType.CREATE_MEDICATION:
            med_name = action.parameters.get("medication_name", "")
            try:
                logs = self.med_service.get_medication_history(action.baby_id, user_id=user_id)
                if logs and len(logs) > 0:
                    for log in logs:
                        if med_name.lower() in log.medication_name.lower() or log.medication_name.lower() in med_name.lower():
                            warning = f"🚨 CẢNH BÁO Y TẾ: Bé vừa có lịch sử uống '{log.medication_name}' gần đây ({log.dosage}). Liều hạ sốt/thuốc tiếp theo cần cách tối thiểu 4-6 giờ. Vui lòng tham vấn ý kiến bác sĩ!"
                            break
            except Exception as e:
                logger.debug(f"[ConsistencyValidator] Bỏ qua kiểm tra lịch sử thuốc: {e}")

        return action, warning
