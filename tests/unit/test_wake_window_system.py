"""
Unit Tests for Wake Window Prediction System
============================================
Kiểm thử toàn diện hệ thống theo Bằng sáng chế US 20250292903:
1. Test Global Model Inference.
2. Test Personalization: Bé A & Bé B cùng tuổi nhưng khác lịch sử 5 ngày -> Dự đoán khác nhau.
3. Test Last-5-Day representation extraction.
4. Test Cold-Start handling (0 days history).
5. Test Safety Guardrails & Expert Baseline fallback.
6. Test Anomaly Trigger -> Expert Value + LLM Reasoner.
"""

import os
import sys
import unittest
import asyncio
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.modules.sleep.wake_window_schemas import (
    WakeWindowFeatureVector,
    Last5DaysHistoryRepresentation,
    SingleDaySleepRepresentation,
)
from app.modules.sleep.safety_guardrails import SafetyGuardrailEngine, get_expert_baseline_config
from app.modules.sleep.feature_engineering import FeatureEngineeringEngine
from app.modules.sleep.wake_window_predictor import (
    GlobalLightGBMPredictor,
    WakeWindowPredictionService,
)


class TestWakeWindowPredictionSystem(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.now = datetime(2026, 8, 23, 13, 0, tzinfo=timezone.utc)

    def test_expert_baseline_config(self):
        """Kiểm tra bảng chuẩn chuyên gia theo tháng tuổi"""
        cfg_5m = get_expert_baseline_config(5.5, nap_number=2)
        self.assertEqual(cfg_5m["expert_ww"], 135)
        self.assertEqual(cfg_5m["min_safe"], 90)
        self.assertEqual(cfg_5m["max_safe"], 165)
        self.assertEqual(cfg_5m["max_dev"], 30)

        cfg_7m = get_expert_baseline_config(7.0, nap_number=2)
        self.assertEqual(cfg_7m["expert_ww"], 165)

        cfg_2m = get_expert_baseline_config(1.5)
        self.assertEqual(cfg_2m["expert_ww"], 75)

    def test_personalization_different_babies_same_global_model(self):
        """
        TEST CỐT LÕI CỦA PATENT:
        Bé A và Bé B có cùng tháng tuổi (6.5 tháng) nhưng lịch sử 5 ngày khác nhau.
        Cùng một Global LightGBM Model phải suy luận ra 2 kết quả dự đoán khác nhau.
        """
        # Bé A: Cơ địa thức lâu hơn (~155 phút)
        features_a = WakeWindowFeatureVector(
            age_months=6.5,
            age_days=198,
            nap_number=2,
            day_start_minutes=420,
            previous_night_end_minutes=390,
            previous_wake_window_minutes=150,
            previous_nap_minutes=75,
            previous_sleep_duration_minutes=75,
            data_days_available=5,
            last_5_days_history=Last5DaysHistoryRepresentation(
                avg_wake_window_minutes=155.0,
                std_wake_window_minutes=10.0,
                avg_nap_duration_minutes=70.0,
                avg_night_sleep_hours=11.0,
                avg_naps_count_per_day=3.0,
            )
        )

        # Bé B: Cơ địa cần ngủ nhiều hơn (~115 phút)
        features_b = WakeWindowFeatureVector(
            age_months=6.5,
            age_days=198,
            nap_number=2,
            day_start_minutes=420,
            previous_night_end_minutes=390,
            previous_wake_window_minutes=115,
            previous_nap_minutes=75,
            previous_sleep_duration_minutes=75,
            data_days_available=5,
            last_5_days_history=Last5DaysHistoryRepresentation(
                avg_wake_window_minutes=115.0,
                std_wake_window_minutes=8.0,
                avg_nap_duration_minutes=70.0,
                avg_night_sleep_hours=11.5,
                avg_naps_count_per_day=3.0,
            )
        )

        pred_a = GlobalLightGBMPredictor.predict_raw(features_a)
        pred_b = GlobalLightGBMPredictor.predict_raw(features_b)

        print(f"[TEST PERSONALIZATION] Bé A: {pred_a:.1f}p | Bé B: {pred_b:.1f}p")
        self.assertNotEqual(round(pred_a), round(pred_b))
        self.assertGreater(pred_a, pred_b)

    async def test_cold_start_policy(self):
        """Kiểm tra Cold-Start (bé mới tạo tài khoản, 0 ngày dữ liệu)"""
        features_cold = WakeWindowFeatureVector(
            age_months=4.5,
            age_days=137,
            nap_number=2,
            day_start_minutes=420,
            previous_night_end_minutes=390,
            previous_wake_window_minutes=120,
            previous_nap_minutes=60,
            previous_sleep_duration_minutes=60,
            data_days_available=0,
            last_5_days_history=None
        )

        resp = await WakeWindowPredictionService.predict_next_wake_window(
            baby_id="test_new_baby",
            features=features_cold,
            current_time=self.now
        )

        self.assertEqual(resp.model_source, "EXPERT_BASELINE_COLD_START")
        self.assertEqual(resp.predicted_wake_window_minutes, 135)
        self.assertFalse(resp.is_anomaly_case)

    async def test_normal_case_uses_pure_ml(self):
        """Kiểm tra luồng bình thường: Dự đoán hợp lý -> Dùng thuần ML (<5ms, không gọi LLM)"""
        features_normal = WakeWindowFeatureVector(
            age_months=6.0,
            age_days=180,
            nap_number=2,
            day_start_minutes=420,
            previous_night_end_minutes=390,
            previous_wake_window_minutes=135,
            previous_nap_minutes=60,
            previous_sleep_duration_minutes=60,
            data_days_available=5,
            last_5_days_history=Last5DaysHistoryRepresentation(
                avg_wake_window_minutes=135.0,
                std_wake_window_minutes=12.0,
                avg_nap_duration_minutes=60.0,
                avg_night_sleep_hours=11.0,
                avg_naps_count_per_day=3.0,
            )
        )

        resp = await WakeWindowPredictionService.predict_next_wake_window(
            baby_id="leo_normal",
            features=features_normal,
            current_time=self.now
        )

        self.assertEqual(resp.model_source, "LIGHTGBM_NORMAL")
        self.assertFalse(resp.is_anomaly_case)
        self.assertIsNone(resp.anomaly_reason)
        self.assertIn("Bé sinh hoạt đều đặn", resp.parental_guidance)

    async def test_anomaly_case_triggers_expert_value_and_llm(self):
        """
        Kiểm tra luồng bất thường:
        Giả lập ML dự đoán lệch quá xa (ví dụ: 260 phút cho bé 4 tháng)
        -> Tự động khóa Expert Value & Kích hoạt LLM điều tra ngữ cảnh y khoa.
        """
        # Cố tình đưa input làm ML tính ra con số quá lớn (outlier)
        features_anomaly = WakeWindowFeatureVector(
            age_months=3.5, # Chuẩn 100p [60 - 120]
            age_days=105,
            nap_number=1,
            day_start_minutes=420,
            previous_night_end_minutes=390,
            previous_wake_window_minutes=250, # Đã thức quá lâu
            previous_nap_minutes=0,
            previous_sleep_duration_minutes=700,
            data_days_available=5,
            last_5_days_history=Last5DaysHistoryRepresentation(
                avg_wake_window_minutes=240.0, # Quá bất thường
                std_wake_window_minutes=15.0,
                avg_nap_duration_minutes=60.0,
                avg_night_sleep_hours=11.0,
                avg_naps_count_per_day=3.0,
            )
        )

        health_logs = [
            {"type": "fever", "temperature": 38.4, "created_at": self.now.isoformat()}
        ]

        resp = await WakeWindowPredictionService.predict_next_wake_window(
            baby_id="leo_fever",
            features=features_anomaly,
            health_logs=health_logs,
            current_time=self.now
        )

        self.assertEqual(resp.model_source, "EXPERT_VALUE_PLUS_LLM")
        self.assertTrue(resp.is_anomaly_case)
        self.assertIsNotNone(resp.anomaly_reason)
        self.assertIsNotNone(resp.parental_guidance)
        # Kết quả phải nằm trong giới hạn an toàn [60, 120]
        self.assertGreaterEqual(resp.predicted_wake_window_minutes, 60)
        self.assertLessEqual(resp.predicted_wake_window_minutes, 125)

    def test_feature_engineering_extraction(self):
        """Kiểm tra trích xuất đặc trưng từ danh sách raw sleep logs"""
        mock_logs = [
            {"action": "wake", "start_time": (self.now - timedelta(days=1, hours=6)).isoformat(), "duration_minutes": 60},
            {"action": "wake", "start_time": (self.now - timedelta(hours=4)).isoformat(), "duration_minutes": 45},
            {"action": "wake", "start_time": (self.now - timedelta(hours=1)).isoformat(), "duration_minutes": 30},
        ]

        bday = (self.now - timedelta(days=180)).date().isoformat()
        features = FeatureEngineeringEngine.extract_features_from_logs(
            baby_id="test_extract",
            birthday_str=bday,
            sleep_logs=mock_logs,
            current_time=self.now
        )

        self.assertAlmostEqual(features.age_months, 5.9, delta=0.2)
        self.assertGreaterEqual(features.data_days_available, 1)
        self.assertIsNotNone(features.last_5_days_history)


if __name__ == "__main__":
    unittest.main()
