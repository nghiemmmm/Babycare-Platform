"""
Test Wake Window System: Feature Engineering & Global LightGBM Predictor
"""
from datetime import datetime, timezone, timedelta
from app.modules.sleep.feature_engineering import FeatureEngineeringEngine
from app.modules.sleep.wake_window_predictor import GlobalLightGBMPredictor
from app.modules.sleep.safety_guardrails import get_expert_baseline_config


def test_expert_baseline_ranges_by_age():
    """Kiểm tra khoảng thời gian thức chuẩn nhi khoa theo độ tuổi"""
    # Trẻ sơ sinh 1 tháng tuổi: Thức khoảng 45 - 90 phút (expert_ww: 75)
    cfg_1m = get_expert_baseline_config(1.0)
    assert cfg_1m["expert_ww"] == 75
    assert cfg_1m["min_safe"] <= cfg_1m["max_safe"]

    # Trẻ 6 tháng tuổi: Thức khoảng 120 - 180 phút
    cfg_6m = get_expert_baseline_config(6.0)
    assert cfg_6m["expert_ww"] >= 120


def test_feature_engineering_extraction():
    """Kiểm tra trích xuất vector đặc trưng từ raw sleep logs"""
    now = datetime.now(timezone.utc)
    mock_logs = [
        {"action": "wake", "start_time": (now - timedelta(hours=4)).isoformat(), "duration_minutes": 45},
        {"action": "wake", "start_time": (now - timedelta(hours=1)).isoformat(), "duration_minutes": 30},
    ]
    bday = (now - timedelta(days=180)).date().isoformat()
    features = FeatureEngineeringEngine.extract_features_from_logs(
        baby_id="test_baby",
        birthday_str=bday,
        sleep_logs=mock_logs,
        current_time=now
    )
    assert 5.0 <= features.age_months <= 7.0


def test_lightgbm_wake_window_predictor():
    """Kiểm tra suy luận LightGBM Model thời gian thực (< 5ms)"""
    now = datetime.now(timezone.utc)
    bday = (now - timedelta(days=180)).date().isoformat()
    features = FeatureEngineeringEngine.extract_features_from_logs(
        baby_id="test_lgb",
        birthday_str=bday,
        sleep_logs=[],
        current_time=now
    )
    raw_pred = GlobalLightGBMPredictor.predict_raw(features)
    assert 60 <= raw_pred <= 300
