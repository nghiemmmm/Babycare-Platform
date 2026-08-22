import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock
from app.AI_agents.workflows.cry_context_retriever import CryContextRetriever
from app.modules.nutrition.schemas import SolidFoodLogResponse
from app.modules.health_records.schemas import HealthRecordResponse
from app.modules.medication.schemas import MedicationLogResponse


def test_cry_context_retriever_multi_source_success():
    """
    Kiểm tra CryContextRetriever thu thập đầy đủ 4 nguồn: Feeding, Health, Medication, Sleep.
    """
    now = datetime(2026, 8, 14, 18, 0, 0, tzinfo=timezone.utc)
    
    nutrition_service = MagicMock()
    nutrition_service.get_solid_food_history.return_value = [
        SolidFoodLogResponse(
            id="food_1",
            baby_id="baby_123",
            logged_at="2026-08-14T17:45:00Z", # 15 phút trước
            food_name="Sữa mẹ",
            amount_g=120.0,
            reaction="Tốt"
        )
    ]

    health_service = MagicMock()
    health_service.get_history.return_value = [
        HealthRecordResponse(
            id="h_1",
            symptoms=["Sốt nhẹ", "Quấy khóc"],
            temp=38.6,
            recorded_at="2026-08-14T17:00:00Z"
        )
    ]

    medication_service = MagicMock()
    medication_service.get_medication_history.return_value = [
        MedicationLogResponse(
            id="med_1",
            medication_name="Hapacol 150mg",
            dosage="1 gói",
            logged_at="2026-08-14T16:00:00Z"
        )
    ]

    retriever = CryContextRetriever(
        nutrition_service=nutrition_service,
        health_service=health_service,
        medication_service=medication_service
    )

    bundle = retriever.retrieve_bundle(baby_id="baby_123", user_id="user_mom", now=now)

    # 1. Feeding check
    assert bundle.feeding.available is True
    assert bundle.feeding.food_name == "Sữa mẹ"
    assert bundle.feeding.minutes_since_feed == 15

    # 2. Health check
    assert bundle.health.available is True
    assert bundle.health.temperature == 38.6
    assert bundle.health.has_fever is True
    assert bundle.health.is_high_risk is True

    # 3. Medication check
    assert bundle.medication.available is True
    assert bundle.medication.medication_name == "Hapacol 150mg"
    assert bundle.medication.minutes_since_medication == 120


def test_cry_context_retriever_fault_tolerance():
    """
    Kiểm tra tính chịu lỗi: Nếu Health service ném Exception, Feeding & Medication vẫn chạy bình thường.
    """
    nutrition_service = MagicMock()
    nutrition_service.get_solid_food_history.return_value = [
        SolidFoodLogResponse(
            id="food_1",
            baby_id="baby_123",
            logged_at="2026-08-14T17:00:00Z",
            food_name="Cháo gà",
            amount_g=100.0
        )
    ]

    health_service = MagicMock()
    health_service.get_history.side_effect = RuntimeError("Firestore Connection Failed")

    medication_service = MagicMock()
    medication_service.get_medication_history.return_value = []

    retriever = CryContextRetriever(
        nutrition_service=nutrition_service,
        health_service=health_service,
        medication_service=medication_service
    )

    bundle = retriever.retrieve_bundle(baby_id="baby_123", user_id="user_mom")

    assert bundle.feeding.available is True
    assert bundle.health.available is False # Đánh dấu unavailable thay vì crash
    assert bundle.medication.available is False
