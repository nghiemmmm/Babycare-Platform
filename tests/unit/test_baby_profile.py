from unittest.mock import patch, MagicMock
import pytest
from app.modules.baby.schemas import BabyCreate, BabyResponse
from app.modules.baby.service import BabyService
from app.modules.growth_tracking.schemas import GrowthLogCreate, GrowthLogResponse
from app.modules.growth_tracking.service import GrowthTrackingService
from app.shared.exceptions import EntityNotFoundError, PermissionDeniedError

# Mock BabyRepository
@pytest.fixture
def mock_baby_repo():
    with patch("app.modules.baby.service.BabyRepository") as mock:
        yield mock.return_value

# Mock GrowthTrackingRepository
@pytest.fixture
def mock_growth_repo():
    with patch("app.modules.growth_tracking.service.GrowthTrackingRepository") as mock:
        yield mock.return_value

def test_create_baby(mock_baby_repo):
    service = BabyService(repository=mock_baby_repo)
    baby_in = BabyCreate(name="Sophia", birth_date="2026-01-01", gender="girl")
    
    mock_baby_repo.create.side_effect = lambda x: x
    
    result = service.create_baby(baby_in, creator_id="user123")
    
    assert result.name == "Sophia"
    assert result.birth_date == "2026-01-01"
    assert result.gender == "girl"
    assert "user123" in result.guardians
    mock_baby_repo.create.assert_called_once()

def test_get_baby_by_id_success(mock_baby_repo):
    service = BabyService(repository=mock_baby_repo)
    
    db_baby = BabyResponse(
        id="baby123",
        name="Sophia",
        birth_date="2026-01-01",
        gender="girl",
        guardians=["user123"]
    )
    mock_baby_repo.get.return_value = db_baby
    
    result = service.get_baby_by_id("baby123", user_id="user123")
    assert result.id == "baby123"
    assert result.name == "Sophia"

def test_get_baby_by_id_permission_denied(mock_baby_repo):
    service = BabyService(repository=mock_baby_repo)
    
    db_baby = BabyResponse(
        id="baby123",
        name="Sophia",
        birth_date="2026-01-01",
        gender="girl",
        guardians=["user123"]
    )
    mock_baby_repo.get.return_value = db_baby
    
    with pytest.raises(PermissionDeniedError):
        service.get_baby_by_id("baby123", user_id="intruder_id")

def test_get_baby_by_id_not_found(mock_baby_repo):
    service = BabyService(repository=mock_baby_repo)
    mock_baby_repo.get.return_value = None
    
    with pytest.raises(EntityNotFoundError):
        service.get_baby_by_id("invalid_id", user_id="user123")

def test_add_growth_log_success(mock_growth_repo):
    # Mock BabyService
    mock_baby_service = MagicMock()
    mock_baby_service.get_baby_by_id.return_value = MagicMock()
    
    service = GrowthTrackingService(baby_service=mock_baby_service)
    
    log_in = GrowthLogCreate(height=70.5, weight=8.2, head_circumference=43.0)
    
    mock_growth_repo.create.side_effect = lambda x: x
    
    result = service.add_growth_log(baby_id="baby123", log_in=log_in, user_id="user123")
    
    assert result.height == 70.5
    assert result.weight == 8.2
    assert result.head_circumference == 43.0
    mock_baby_service.get_baby_by_id.assert_called_once_with("baby123", "user123")
    mock_growth_repo.create.assert_called_once()
