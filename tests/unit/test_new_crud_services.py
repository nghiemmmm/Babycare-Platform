from unittest.mock import patch, MagicMock
import pytest
from app.shared.exceptions import EntityNotFoundError

from app.modules.medication.schemas import MedicationLogCreate, MedicationLogResponse
from app.modules.medication.service import MedicationService
from app.modules.nutrition.schemas import SolidFoodLogCreate, SolidFoodLogResponse
from app.modules.nutrition.service import SolidFoodService


# Mock MedicationRepository
@pytest.fixture
def mock_medication_repo():
    with patch("app.modules.medication.service.MedicationRepository") as mock:
        yield mock.return_value


# Mock SolidFoodRepository
@pytest.fixture
def mock_solid_food_repo():
    with patch("app.modules.nutrition.service.SolidFoodRepository") as mock:
        yield mock.return_value


def test_add_medication_log(mock_medication_repo):
    # Mock BabyService
    mock_baby_service = MagicMock()
    mock_baby_service.get_baby_by_id.return_value = MagicMock()
    
    service = MedicationService(baby_service=mock_baby_service)
    
    log_in = MedicationLogCreate(
        logged_at="2026-07-15T16:30:00Z",
        medication_name="Hapacol",
        dosage="150mg",
        prescribed_by="Dr. Watson"
    )
    
    mock_medication_repo.create.side_effect = lambda x: x
    
    result = service.add_medication_log(baby_id="baby123", log_in=log_in, user_id="user123")
    
    assert result.medication_name == "Hapacol"
    assert result.dosage == "150mg"
    assert result.prescribed_by == "Dr. Watson"
    mock_baby_service.get_baby_by_id.assert_called_once_with("baby123", "user123")
    mock_medication_repo.create.assert_called_once()


def test_get_medication_history(mock_medication_repo):
    mock_baby_service = MagicMock()
    mock_baby_service.get_baby_by_id.return_value = MagicMock()
    
    service = MedicationService(baby_service=mock_baby_service)
    
    logs = [
        MedicationLogResponse(logged_at="2026-07-15T10:00:00Z", medication_name="Vitamin D", dosage="2 drops"),
        MedicationLogResponse(logged_at="2026-07-15T12:00:00Z", medication_name="Hapacol", dosage="150mg")
    ]
    mock_medication_repo.list.return_value = logs
    
    result = service.get_medication_history(baby_id="baby123", user_id="user123")
    
    # Must sort by logged_at descending
    assert len(result) == 2
    assert result[0].logged_at == "2026-07-15T12:00:00Z"
    mock_baby_service.get_baby_by_id.assert_called_once_with("baby123", "user123")


def test_delete_medication_log_success(mock_medication_repo):
    mock_baby_service = MagicMock()
    mock_baby_service.get_baby_by_id.return_value = MagicMock()
    
    service = MedicationService(baby_service=mock_baby_service)
    
    mock_medication_repo.get.return_value = MagicMock()
    mock_medication_repo.delete.return_value = True
    
    result = service.delete_medication_log(baby_id="baby123", log_id="log123", user_id="user123")
    
    assert result is True
    mock_medication_repo.delete.assert_called_once_with("log123")


def test_delete_medication_log_not_found(mock_medication_repo):
    mock_baby_service = MagicMock()
    mock_baby_service.get_baby_by_id.return_value = MagicMock()
    
    service = MedicationService(baby_service=mock_baby_service)
    
    mock_medication_repo.get.return_value = None
    
    with pytest.raises(EntityNotFoundError):
        service.delete_medication_log(baby_id="baby123", log_id="log123", user_id="user123")


def test_add_solid_food_log(mock_solid_food_repo):
    mock_baby_service = MagicMock()
    mock_baby_service.get_baby_by_id.return_value = MagicMock()
    
    service = SolidFoodService(baby_service=mock_baby_service)
    
    log_in = SolidFoodLogCreate(
        logged_at="2026-07-15T16:30:00Z",
        food_name="Apple Puree",
        amount_g=80.0,
        reaction="like"
    )
    
    mock_solid_food_repo.create.side_effect = lambda x: x
    
    result = service.add_solid_food_log(baby_id="baby123", log_in=log_in, user_id="user123")
    
    assert result.food_name == "Apple Puree"
    assert result.amount_g == 80.0
    assert result.reaction == "like"
    mock_baby_service.get_baby_by_id.assert_called_once_with("baby123", "user123")
    mock_solid_food_repo.create.assert_called_once()
