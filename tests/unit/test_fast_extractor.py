import pytest
from app.AI_agents.core.fast_extractor import FastTrackingExtractor

def test_extract_feeding():
    res1 = FastTrackingExtractor.extract_feeding("bé vừa bú 150ml sữa công thức lúc 3h")
    assert res1 is not None
    assert res1["activity_type"] == "feeding"
    assert res1["amount_g"] == 150

    res2 = FastTrackingExtractor.extract_feeding("bú 120ml")
    assert res2 is not None
    assert res2["activity_type"] == "feeding"
    assert res2["amount_g"] == 120

def test_extract_medication_and_aliases():
    res = FastTrackingExtractor.extract_medication("cho bé uống hapa coi 150mg")
    assert res is not None
    assert res["activity_type"] == "medication"
    assert res["medication_name"] == "Hapacol"
    assert res["dosage"] == "150mg"

def test_extract_growth_and_slang():
    res = FastTrackingExtractor.extract_growth("chiều cao 66cm cân nặng 7 ký rưỡi")
    assert res is not None
    assert res["activity_type"] == "growth"
    assert res["height"] == 66.0
    assert res["weight"] == 7.5

def test_extract_temperature():
    res = FastTrackingExtractor.extract_temperature("nhiệt độ bé là 38.5 độ c")
    assert res is not None
    assert res["activity_type"] == "symptom"
    assert res["temperature"] == 38.5

def test_deterministic_read_queries():
    res1 = FastTrackingExtractor.try_extract("cữ bú gần nhất của bé khi nào?")
    assert res1 is not None
    assert res1["activity_type"] == "read_last_feed"

    res2 = FastTrackingExtractor.try_extract("chiều cao và cân nặng gần nhất của bé")
    assert res2 is not None
    assert res2["activity_type"] == "read_growth_profile"

def test_mixed_query_rejection():
    # Mixed query (tracking + thắc mắc) -> NÊN nhả ra (returns None) để nhường LLM & RAG xử lý
    res = FastTrackingExtractor.try_extract("Bé vừa bú 150ml xong thì nôn trớ hết ra ngoài có sao không?")
    assert res is None

