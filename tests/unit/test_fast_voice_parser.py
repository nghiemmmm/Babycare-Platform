import pytest
import time
from app.AI_agents.core.fast_voice_parser import FastVoiceParser


# ============================================================================
# TEST SUITE MA TRẬN 50+ TEST CASES CHO FAST VOICE PARSER
# ============================================================================

# ── 1. FEEDING TESTS (10 Cases) ──────────────────────────────────────────────

def test_feeding_standard_formula():
    res = FastVoiceParser.parse("Bé vừa bú 150ml sữa công thức")
    assert res.intent == "feeding"
    assert res.canonical_data["amount"] == 150.0
    assert res.canonical_data["feed_type"] == "Formula"
    assert len(res.missing_fields) == 0

def test_feeding_breastmilk():
    res = FastVoiceParser.parse("Bé bú 120ml sữa mẹ")
    assert res.intent == "feeding"
    assert res.canonical_data["amount"] == 120.0
    assert res.canonical_data["feed_type"] == "Breast"

def test_feeding_vietnamese_number_150():
    res = FastVoiceParser.parse("Bé ăn một trăm năm mươi ml sữa")
    assert res.intent == "feeding"
    assert res.canonical_data["amount"] == 150.0

def test_feeding_vietnamese_number_210():
    res = FastVoiceParser.parse("Bé uống hai trăm mốt ml sữa công thức")
    assert res.intent == "feeding"
    assert res.canonical_data["amount"] == 210.0

def test_feeding_cc_unit():
    res = FastVoiceParser.parse("Bé bú 180 cc sữa mẹ")
    assert res.intent == "feeding"
    assert res.canonical_data["amount"] == 180.0
    assert res.canonical_data["feed_type"] == "Breast"

def test_feeding_bottle_unit():
    res = FastVoiceParser.parse("Bé uống 1 bình sữa")
    assert res.intent == "feeding"
    assert res.canonical_data["amount"] == 150.0

def test_feeding_solids_porridge():
    res = FastVoiceParser.parse("Bé ăn 80g cháo bí đỏ")
    assert res.intent == "feeding"
    assert res.canonical_data["amount"] == 80.0
    assert res.canonical_data["feed_type"] == "Solids"

def test_feeding_solids_avocado():
    res = FastVoiceParser.parse("Cho bé ăn dặm bơ nghiền")
    assert res.intent == "feeding"
    assert res.canonical_data["feed_type"] == "Solids"

def test_feeding_missing_amount_gives_chips():
    res = FastVoiceParser.parse("Bé vừa bú sữa mẹ")
    assert res.intent == "feeding"
    assert res.canonical_data["amount"] is None
    assert "amount" in res.missing_fields
    assert "120ml" in res.suggested_chips

def test_feeding_excessive_amount_warning():
    res = FastVoiceParser.parse("Bé uống 450ml sữa công thức")
    assert res.intent == "feeding"
    assert any("400ml" in w for w in res.warnings)


# ── 2. MEDICATION TESTS (10 Cases) ───────────────────────────────────────────

def test_medication_hapacol_standard():
    res = FastVoiceParser.parse("Cho bé uống 1 gói Hapacol 150mg")
    assert res.intent == "medication"
    assert res.canonical_data["medication_name"] == "Hapacol 150mg"
    assert res.canonical_data["dosage"] == "150mg"

def test_medication_paracetamol():
    res = FastVoiceParser.parse("Bé uống Paracetamol 100mg")
    assert res.intent == "medication"
    assert res.canonical_data["medication_name"] == "Paracetamol"
    assert res.canonical_data["dosage"] == "100mg"

def test_medication_vitamin_d3():
    res = FastVoiceParser.parse("Cho bé uống 2 giọt Vitamin D3")
    assert res.intent == "medication"
    assert res.canonical_data["medication_name"] == "Vitamin D3 K2"
    assert res.canonical_data["dosage"] == "2giọt"

def test_medication_siro_ho():
    res = FastVoiceParser.parse("Uống 5ml siro ho")
    assert res.intent == "medication"
    assert res.canonical_data["medication_name"] == "Siro ho Nhi khoa"
    assert res.canonical_data["dosage"] == "5ml"

def test_medication_half_packet():
    res = FastVoiceParser.parse("Bé uống nửa gói hapacol")
    assert res.intent == "medication"
    assert "hapacol" in res.canonical_data["medication_name"].lower()
    assert res.canonical_data["dosage"] == "0.5gói"

def test_medication_one_tablet():
    res = FastVoiceParser.parse("Bé uống 1 viên thuốc hạ sốt")
    assert res.intent == "medication"
    assert res.canonical_data["dosage"] == "1viên"

def test_medication_missing_dosage():
    res = FastVoiceParser.parse("Cho bé uống thuốc hạ sốt hapacol")
    assert res.intent == "medication"
    assert res.canonical_data["medication_name"] == "Hapacol 150mg"
    assert res.canonical_data["dosage"] == "150mg"

def test_medication_asr_typo_ha_pa_col():
    res = FastVoiceParser.parse("Bé uống ha pa col 150mg")
    assert res.intent == "medication"
    assert res.canonical_data["dosage"] == "150mg"

def test_medication_asr_typo_pa_ra_ce_ta_mol():
    res = FastVoiceParser.parse("Bé uống pa ra ce ta mol 80mg")
    assert res.intent == "medication"
    assert "paracetamol" in res.canonical_data["medication_name"].lower()
    assert res.canonical_data["dosage"] == "80mg"

def test_medication_drops_unit():
    res = FastVoiceParser.parse("Bé uống 3 giọt vitamin")
    assert res.intent == "medication"
    assert res.canonical_data["dosage"] == "3giọt"


# ── 3. GROWTH DISENGAGEMENT & DIAPER / SLEEP EXPANDED TESTS ─────────────────

def test_growth_not_in_quick_voice():
    res = FastVoiceParser.parse("Bé cân nặng 7.2kg")
    # Growth đã được tách riêng khỏi Voice Quick Log để quản lý tại Tab Tăng trưởng WHO
    assert res.intent == "unknown"

def test_growth_height_not_in_quick_voice():
    res = FastVoiceParser.parse("Bé cao 66cm")
    assert res.intent == "unknown"



# ── 4. DIAPER & SLEEP TESTS (10 Cases) ───────────────────────────────────────

def test_diaper_wet():
    res = FastVoiceParser.parse("Bé vừa đi tè ướt tã")
    assert res.intent == "diaper"
    assert res.canonical_data["type"] == "Wet"

def test_diaper_dirty_ia():
    res = FastVoiceParser.parse("Bé đi ị bẩn bỉm")
    assert res.intent == "diaper"
    assert res.canonical_data["type"] == "Dirty"

def test_diaper_dirty_phan():
    res = FastVoiceParser.parse("Bé đi ngoài ra phân mềm")
    assert res.intent == "diaper"
    assert res.canonical_data["type"] == "Dirty"

def test_diaper_dam_bim():
    res = FastVoiceParser.parse("Thay bỉm cho bé vừa tè dầm")
    assert res.intent == "diaper"
    assert res.canonical_data["type"] == "Wet"

def test_sleep_wake():
    res = FastVoiceParser.parse("Bé vừa ngủ dậy lúc 8h")
    assert res.intent == "sleep"
    assert res.canonical_data["action"] == "wake"

def test_sleep_start():
    res = FastVoiceParser.parse("Bé bắt đầu đi ngủ")
    assert res.intent == "sleep"
    assert res.canonical_data["action"] == "start_sleep"

def test_sleep_nap():
    res = FastVoiceParser.parse("Bé chợp mắt được 45 phút")
    assert res.intent == "sleep"

def test_sleep_into_bed():
    res = FastVoiceParser.parse("Cho bé vào giấc ngủ đêm")
    assert res.intent == "sleep"
    assert res.canonical_data["action"] == "start_sleep"

def test_compound_feed_then_sleep():
    res = FastVoiceParser.parse("Bé bú 150ml sữa rồi ngủ")
    assert res.intent == "feeding"
    assert res.canonical_data["amount"] == 150.0

def test_compound_diaper_then_feed():
    res = FastVoiceParser.parse("Thay tã rồi cho bé bú 120ml sữa")
    assert res.intent == "feeding"
    assert res.canonical_data["amount"] == 120.0


# ── 5. EDGE CASES & SAFETY GUARDRAILS (10 Cases) ─────────────────────────────

def test_negation_chua_uong_thuoc():
    res = FastVoiceParser.parse("Bé chưa uống thuốc hạ sốt")
    assert res.intent == "medication"
    assert any("chưa/không" in w for w in res.warnings)
    assert res.confidence < 0.50

def test_future_toi_nay():
    res = FastVoiceParser.parse("Tối nay cho bé uống 1 gói thuốc")
    assert res.intent == "medication"
    assert any("tương lai" in w for w in res.warnings)

def test_empty_transcript():
    res = FastVoiceParser.parse("")
    assert res.success is False
    assert res.intent == "unknown"
    assert res.confidence == 0.0

def test_whitespace_transcript():
    res = FastVoiceParser.parse("    ")
    assert res.success is False
    assert res.intent == "unknown"

def test_random_unrelated_text():
    res = FastVoiceParser.parse("Thời tiết hôm nay trời nhiều mây")
    assert res.intent == "unknown"
    assert res.confidence < 0.30

def test_uppercase_punctuation():
    res = FastVoiceParser.parse("BÉ VỪA BÚ 160ML SỮA CÔNG THỨC!!!")
    assert res.intent == "feeding"
    assert res.canonical_data["amount"] == 160.0

def test_word_nam_chuc():
    res = FastVoiceParser.parse("Bé bú năm chục ml sữa mẹ")
    assert res.intent == "feeding"
    assert res.canonical_data["amount"] == 50.0

def test_word_hai_tram():
    res = FastVoiceParser.parse("Bé bú hai trăm ml sữa công thức")
    assert res.intent == "feeding"
    assert res.canonical_data["amount"] == 200.0

def test_word_sau_muoi():
    res = FastVoiceParser.parse("Bé ăn sáu mươi ml sữa mẹ")
    assert res.intent == "feeding"
    assert res.canonical_data["amount"] == 60.0

def test_parser_latency_under_10ms():
    """Kiểm tra hiệu năng: 1,000 lần parse phải hoàn thành trong < 500ms (trung bình < 0.5ms/lần)."""
    t0 = time.time()
    for _ in range(1000):
        FastVoiceParser.parse("Bé vừa bú 150ml sữa công thức")
    elapsed = time.time() - t0
    assert elapsed < 0.50, f"Parser quá chậm: {elapsed}s cho 1000 lượt"

