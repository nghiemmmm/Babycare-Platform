"""
Test Fast Voice Parser: Bóc tách nhật ký giọng nói thành dữ liệu chuẩn hóa
"""
from app.AI_agents.core.fast_voice_parser import FastVoiceParser


def test_parse_feeding_action():
    """Kiểm tra bóc tách hành động bú sữa / ăn dặm"""
    res = FastVoiceParser.parse("Bé vừa bú 150ml sữa công thức")
    assert res.intent == "feeding"
    assert res.canonical_data["amount"] == 150.0
    assert "Formula" in res.canonical_data.get("feed_type", "")


def test_parse_diaper_and_sleep_actions():
    """Kiểm tra bóc tách hành động thay tã và giấc ngủ"""
    res_diaper = FastVoiceParser.parse("Bé vừa tè thay tã ướt")
    assert res_diaper.intent == "diaper"

    res_sleep = FastVoiceParser.parse("Bé ngủ được 45 phút")
    assert res_sleep.intent == "sleep"


def test_parse_medication():
    """Kiểm tra bóc tách hành động uống thuốc"""
    res_med = FastVoiceParser.parse("Cho bé uống 1 gói hạ sốt Hapacol 150mg")
    assert res_med.intent == "medication"
    assert "Hapacol" in res_med.canonical_data["medication_name"]
