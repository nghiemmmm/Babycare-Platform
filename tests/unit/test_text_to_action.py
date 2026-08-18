"""
Unit Tests for Text-to-Action & Multi-Tool Calling Pipeline
===========================================================
Comprehensive Pediatric Test Suite:
1. Single action (Feeding - Formula & Breast)
2. Solid food action (Cháo, Bột, Ăn dặm)
3. Number words conversion (hai trăm mốt -> 210, năm chục -> 50)
4. Slang and shortcuts (1 bình sữa -> 150ml)
5. STT Acoustic Aliases (ha pa col -> hapacol, meo -> ml)
6. Vitamin and Syrup dosages (giọt, ml)
7. Sleep actions (Start sleep & Nap duration)
8. Diaper actions (Wet, Dirty, Both)
9. Medication action with Human Confirmation Gate
10. Multi-Action parallel execution (Compound Feeding + Sleep)
11. Multi-Action compound (Diaper + Feeding)
12. Triple Multi-Action compound (Diaper + Feeding + Sleep)
13. Missing entity / Clarification needed
14. Negation Guardrail
15. Future Temporal Guardrail
16. Idempotency deduplication
17. Tool resilience and error handling
18. Confirmation execution workflow
"""
import pytest
import asyncio
from unittest.mock import MagicMock, patch
from app.AI_agents.actions.schemas import (
    ActionType,
    ActionStatus,
    ActionRiskLevel,
    BabyCareAction,
    ActionConfirmRequest,
    ActionResultItem
)
from app.AI_agents.actions.parser import ActionParserEngine
from app.AI_agents.actions.dispatcher import ActionDispatcher
from app.AI_agents.actions.risk_policy import ActionRiskPolicy


# ─── 1. TEST PARSER & DOMAIN ENTITY EXTRACTION ───────────────────────────────

def test_parse_single_feeding_breast():
    actions = ActionParserEngine.parse_actions("Bé vừa bú 150ml sữa mẹ", baby_id="baby_001")
    assert len(actions) == 1
    act = actions[0]
    assert act.action_type == ActionType.CREATE_FEEDING
    assert act.parameters["amount"] == 150.0
    assert act.parameters["feed_type"] == "Breast"
    assert act.status == ActionStatus.READY_TO_EXECUTE
    assert len(act.missing_fields) == 0


def test_parse_single_feeding_formula():
    actions = ActionParserEngine.parse_actions("Bé uống 180ml sữa công thức", baby_id="baby_001")
    assert len(actions) == 1
    act = actions[0]
    assert act.action_type == ActionType.CREATE_FEEDING
    assert act.parameters["amount"] == 180.0
    assert act.parameters["feed_type"] == "Formula"


def test_parse_solid_food():
    """Ghi nhận cữ ăn dặm bằng gam."""
    actions = ActionParserEngine.parse_actions("Bé ăn 80g cháo bí đỏ", baby_id="baby_001")
    assert len(actions) == 1
    act = actions[0]
    assert act.action_type == ActionType.CREATE_FEEDING
    assert act.parameters["amount"] == 80.0
    assert act.parameters["feed_type"] == "Solids"
    assert act.parameters["unit"] == "g"


def test_parse_vietnamese_word_numbers():
    """Bóc tách chữ số tiếng Việt: hai trăm mốt -> 210, năm chục -> 50."""
    actions1 = ActionParserEngine.parse_actions("Bé uống hai trăm mốt ml sữa công thức", baby_id="baby_001")
    assert actions1[0].parameters["amount"] == 210.0

    actions2 = ActionParserEngine.parse_actions("Bé bú năm chục ml sữa mẹ", baby_id="baby_001")
    assert actions2[0].parameters["amount"] == 50.0


def test_parse_slang_bottle():
    """Nói tắt '1 bình sữa' -> chuẩn hóa thành 150ml."""
    actions = ActionParserEngine.parse_actions("Cho bé uống 1 bình sữa", baby_id="baby_001")
    assert actions[0].parameters["amount"] == 150.0


def test_parse_stt_aliases():
    """Từ điển âm thanh sửa lỗi STT: ha pa col -> hapacol."""
    actions = ActionParserEngine.parse_actions("Bé uống ha pa col 150mg", baby_id="baby_001")
    assert actions[0].action_type == ActionType.CREATE_MEDICATION
    assert actions[0].parameters["dosage"] == "150mg"


def test_parse_vitamin_drops_and_syrup():
    """Bóc tách liều thuốc dạng giọt hoặc siro ml."""
    actions1 = ActionParserEngine.parse_actions("Cho bé uống 2 giọt Vitamin D3", baby_id="baby_001")
    assert actions1[0].parameters["dosage"] == "2giọt"

    actions2 = ActionParserEngine.parse_actions("Uống 5ml siro ho", baby_id="baby_001")
    assert actions2[0].parameters["dosage"] == "5ml"


def test_parse_sleep_start_and_nap():
    actions1 = ActionParserEngine.parse_actions("Cho bé vào giấc ngủ đêm", baby_id="baby_001")
    assert actions1[0].action_type == ActionType.CREATE_SLEEP
    assert actions1[0].parameters["action"] == "start_sleep"

    actions2 = ActionParserEngine.parse_actions("Bé chợp mắt được 45 phút rồi dậy", baby_id="baby_001")
    assert actions2[0].parameters["duration_minutes"] == 45


def test_parse_diaper_wet_dirty_both():
    act_wet = ActionParserEngine.parse_actions("Bé vừa đi tè ướt tã", baby_id="baby_001")
    assert act_wet[0].parameters["diaper_type"] == "Wet"

    act_dirty = ActionParserEngine.parse_actions("Bé vừa đi ngoài ra phân mềm", baby_id="baby_001")
    assert act_dirty[0].parameters["diaper_type"] == "Dirty"

    act_both = ActionParserEngine.parse_actions("Bé vừa đi tè và đi ngoài bẩn bỉm", baby_id="baby_001")
    assert act_both[0].parameters["diaper_type"] == "Both"


def test_parse_medication_requires_confirmation():
    actions = ActionParserEngine.parse_actions("Cho bé uống 1 gói Hapacol 150mg", baby_id="baby_001")
    assert len(actions) == 1
    act = actions[0]
    assert act.action_type == ActionType.CREATE_MEDICATION
    assert act.parameters["dosage"] == "150mg"
    assert act.risk_level == ActionRiskLevel.HIGH
    assert act.requires_confirmation is True


# ─── 2. TEST MULTI-ACTION & COMPOUNDS ────────────────────────────────────────

def test_parse_multi_action_feed_and_sleep():
    """Phân rã 2 hành động độc lập trong 1 câu nói."""
    actions = ActionParserEngine.parse_actions("Bé bú 150ml sữa công thức rồi ngủ 1 tiếng", baby_id="baby_001")
    assert len(actions) == 2
    types = [a.action_type for a in actions]
    assert ActionType.CREATE_FEEDING in types
    assert ActionType.CREATE_SLEEP in types


def test_parse_multi_action_diaper_and_feed():
    actions = ActionParserEngine.parse_actions("Thay tã rồi cho bé bú 120ml sữa", baby_id="baby_001")
    assert len(actions) == 2
    types = [a.action_type for a in actions]
    assert ActionType.CREATE_DIAPER in types
    assert ActionType.CREATE_FEEDING in types


def test_parse_triple_compound_actions():
    """Phân rã 3 hành động cùng lúc: Thay tã + Cữ bú + Giấc ngủ."""
    actions = ActionParserEngine.parse_actions("Thay tã xong cho bé bú 150ml sữa rồi đi ngủ 1 tiếng", baby_id="baby_001")
    assert len(actions) == 3
    types = [a.action_type for a in actions]
    assert ActionType.CREATE_DIAPER in types
    assert ActionType.CREATE_FEEDING in types
    assert ActionType.CREATE_SLEEP in types


# ─── 3. TEST GUARDRAILS & CLARIFICATION ──────────────────────────────────────

def test_parse_missing_amount_needs_clarification():
    """Thiếu trường amount -> không lưu bừa mà trả về clarification prompt và suggested chips."""
    actions = ActionParserEngine.parse_actions("Cho bé bú sữa mẹ", baby_id="baby_001")
    assert len(actions) == 1
    act = actions[0]
    assert act.action_type == ActionType.CREATE_FEEDING
    assert act.status == ActionStatus.NEEDS_CLARIFICATION
    assert "amount" in act.missing_fields
    assert len(act.suggested_chips) > 0


def test_negation_guardrail():
    """Phát hiện câu phủ định -> không sinh Action ghi vào database."""
    actions = ActionParserEngine.parse_actions("Bé chưa uống thuốc hạ sốt", baby_id="baby_001")
    assert len(actions) == 0


def test_future_guardrail():
    """Phát hiện thời gian tương lai -> không sinh Action hoàn thành."""
    actions = ActionParserEngine.parse_actions("Tối nay sẽ cho bé bú 150ml sữa", baby_id="baby_001")
    assert len(actions) == 0


# ─── 4. TEST DISPATCHER & MULTI-TOOL EXECUTION ───────────────────────────────

def test_dispatcher_single_feeding_execution():
    dispatcher = ActionDispatcher()
    actions = ActionParserEngine.parse_actions("Bé vừa bú 150ml sữa mẹ", baby_id="test_baby")
    
    with patch.object(dispatcher.tools[ActionType.CREATE_FEEDING], "execute") as mock_exec:
        async def _mock_run(*args, **kwargs):
            return ActionResultItem(
                action_id="act_1",
                action_type=ActionType.CREATE_FEEDING,
                status=ActionStatus.COMPLETED,
                record_id="feed_123",
                message="Đã ghi nhận cữ bú 150ml Sữa mẹ"
            )
        mock_exec.side_effect = _mock_run
        report = asyncio.run(dispatcher.dispatch(actions, user_id="user_123"))
        assert report.success is True
        assert len(report.executed_actions) == 1
        assert report.executed_actions[0].record_id == "feed_123"


def test_dispatcher_medication_blocks_and_awaits_confirmation():
    """Thuốc phải được đưa vào pending_confirmations thay vì tự động thực thi."""
    dispatcher = ActionDispatcher()
    actions = ActionParserEngine.parse_actions("Cho bé uống 1 gói Hapacol 150mg", baby_id="test_baby")
    
    report = asyncio.run(dispatcher.dispatch(actions, user_id="user_123"))
    assert len(report.executed_actions) == 0
    assert len(report.pending_confirmations) == 1
    assert report.pending_confirmations[0].action_type == ActionType.CREATE_MEDICATION


def test_dispatcher_parallel_multi_tool_execution():
    """Thực thi song song cả 2 tool cho cữ bú và giấc ngủ."""
    dispatcher = ActionDispatcher()
    actions = ActionParserEngine.parse_actions("Bé bú 150ml sữa rồi ngủ 1 tiếng", baby_id="test_baby_parallel")
    
    with patch.object(dispatcher.tools[ActionType.CREATE_FEEDING], "execute") as mock_feed, \
         patch.object(dispatcher.tools[ActionType.CREATE_SLEEP], "execute") as mock_sleep:
        
        async def _mock_feed_run(*args, **kwargs):
            return ActionResultItem(
                action_id="act_feed",
                action_type=ActionType.CREATE_FEEDING,
                status=ActionStatus.COMPLETED,
                record_id="feed_001",
                message="Đã ghi nhận cữ bú 150ml"
            )
        async def _mock_sleep_run(*args, **kwargs):
            return ActionResultItem(
                action_id="act_sleep",
                action_type=ActionType.CREATE_SLEEP,
                status=ActionStatus.COMPLETED,
                record_id="sleep_001",
                message="Đã ghi nhận giấc ngủ 60 phút"
            )
        mock_feed.side_effect = _mock_feed_run
        mock_sleep.side_effect = _mock_sleep_run

        report = asyncio.run(dispatcher.dispatch(actions, user_id="user_123"))
        assert report.success is True
        assert len(report.executed_actions) == 2


def test_dispatcher_partial_failure_resilience():
    """Nếu 1 Tool bị lỗi, Tool còn lại vẫn hoàn tất an toàn."""
    dispatcher = ActionDispatcher()
    actions = ActionParserEngine.parse_actions("Thay tã rồi cho bé bú 120ml sữa", baby_id="test_baby_partial")
    
    with patch.object(dispatcher.tools[ActionType.CREATE_DIAPER], "execute") as mock_diaper, \
         patch.object(dispatcher.tools[ActionType.CREATE_FEEDING], "execute") as mock_feed:
        
        async def _mock_diaper_run(*args, **kwargs):
            return ActionResultItem(
                action_id="act_diaper",
                action_type=ActionType.CREATE_DIAPER,
                status=ActionStatus.FAILED,
                message="Lỗi kết nối tã bỉm",
                error="ConnectionError"
            )
        async def _mock_feed_run(*args, **kwargs):
            return ActionResultItem(
                action_id="act_feed",
                action_type=ActionType.CREATE_FEEDING,
                status=ActionStatus.COMPLETED,
                record_id="feed_120",
                message="Đã ghi nhận cữ bú 120ml"
            )
        mock_diaper.side_effect = _mock_diaper_run
        mock_feed.side_effect = _mock_feed_run

        report = asyncio.run(dispatcher.dispatch(actions, user_id="user_123"))
        assert len(report.executed_actions) == 1
        assert len(report.failed_actions) == 1
        assert report.executed_actions[0].record_id == "feed_120"


def test_idempotency_deduplication():
    """Gửi liên tiếp cùng 1 action trong khoảng thời gian ngắn -> bị lọc bỏ trùng lặp."""
    dispatcher = ActionDispatcher()
    actions1 = ActionParserEngine.parse_actions("Bé vừa bú 150ml sữa mẹ", baby_id="test_baby_idem")
    
    with patch.object(dispatcher.tools[ActionType.CREATE_FEEDING], "execute") as mock_exec:
        async def _mock_run(*args, **kwargs):
            return ActionResultItem(
                action_id="act_1",
                action_type=ActionType.CREATE_FEEDING,
                status=ActionStatus.COMPLETED,
                record_id="feed_123",
                message="Đã ghi nhận cữ bú 150ml Sữa mẹ"
            )
        mock_exec.side_effect = _mock_run
        
        # Lần 1: Thực thi bình thường
        report1 = asyncio.run(dispatcher.dispatch(actions1, user_id="user_123"))
        assert len(report1.executed_actions) == 1

        # Lần 2: Gửi lại ngay lập tức -> bị lọc bởi idempotency
        actions2 = ActionParserEngine.parse_actions("Bé vừa bú 150ml sữa mẹ", baby_id="test_baby_idem")
        report2 = asyncio.run(dispatcher.dispatch(actions2, user_id="user_123"))
        assert len(report2.executed_actions) == 0
        assert any("trùng lặp" in w for w in report2.warnings)


# ─── 5. TEST CONSISTENCY, MULTI-GUARDIAN & MEDICAL GUARDRAILS ─────────────────

def test_physiological_feeding_overflow():
    """Cữ bú > 400ml vượt ngưỡng dung tích dạ dày bé -> Nâng mức HIGH_RISK và yêu cầu xác nhận."""
    dispatcher = ActionDispatcher()
    actions = ActionParserEngine.parse_actions("Bé vừa bú 600ml sữa mẹ", baby_id="baby_overflow")
    
    report = asyncio.run(dispatcher.dispatch(actions, user_id="user_123"))
    assert len(report.executed_actions) == 0
    assert len(report.pending_confirmations) == 1
    assert any("vượt quá dung tích dạ dày" in w for w in report.warnings)


def test_multi_guardian_feeding_collision():
    """Phát hiện cữ bú vừa được ghi nhận gần đây -> Cảnh báo xung đột đa người giám hộ."""
    dispatcher = ActionDispatcher()
    actions = ActionParserEngine.parse_actions("Bé vừa bú 120ml sữa công thức", baby_id="baby_collision")
    
    from app.modules.nutrition.schemas import FeedResponse
    mock_history = [
        FeedResponse(id="feed_01", type="Sữa mẹ", details="150ml Sữa mẹ", amount=150.0, time="08:00")
    ]
    
    with patch.object(dispatcher.consistency_validator.feed_service, "get_feed_history", return_value=mock_history):
        report = asyncio.run(dispatcher.dispatch(actions, user_id="user_guardian_mom"))
        assert len(report.executed_actions) == 0
        assert len(report.pending_confirmations) == 1
        assert any("Đã có một cữ bú" in w for w in report.warnings)


def test_medication_interval_safe_guardrail():
    """Phát hiện thuốc cùng loại được uống trong vòng 4 giờ -> Cảnh báo Đỏ nguy cơ quá liều y tế."""
    dispatcher = ActionDispatcher()
    actions = ActionParserEngine.parse_actions("Cho bé uống 1 gói Hapacol 150mg", baby_id="baby_med_guard")
    
    from app.modules.medication.schemas import MedicationLogResponse
    mock_med_history = [
        MedicationLogResponse(id="med_01", medication_name="Hapacol 150mg", dosage="150mg", logged_at="2026-08-16T17:00:00Z")
    ]
    
    with patch.object(dispatcher.consistency_validator.med_service, "get_medication_history", return_value=mock_med_history):
        report = asyncio.run(dispatcher.dispatch(actions, user_id="user_dad"))
        assert len(report.pending_confirmations) == 1
        assert any("🚨 CẢNH BÁO Y TẾ" in w for w in report.warnings)


def test_sleep_action_auto_calculates_cycle_timestamps():
    """Thức dậy sau 45 phút -> Tự động tính lùi chu kỳ ngủ start_time và end_time."""
    from app.AI_agents.actions.tools import SleepActionTool
    sleep_tool = SleepActionTool()
    
    with patch.object(sleep_tool.sleep_service, "add_sleep_log") as mock_add:
        from app.modules.sleep.schemas import SleepLogResponse
        mock_add.return_value = SleepLogResponse(id="sleep_rec_123", baby_id="baby_sl", action="wake", duration_minutes=45, logged_at="2026-08-16T18:00:00Z")
        
        res = asyncio.run(sleep_tool.execute(
            action_id="act_sl",
            baby_id="baby_sl",
            parameters={"action": "wake", "duration_minutes": 45},
            user_id="user_123"
        ))
        assert res.status == ActionStatus.COMPLETED
        assert res.record_id == "sleep_rec_123"
        # Kiểm tra SleepLogCreate được gọi có đủ start_time và end_time
        args, kwargs = mock_add.call_args
        log_in = kwargs.get("log_in") or args[1]
        assert log_in.start_time is not None
        assert log_in.end_time is not None

