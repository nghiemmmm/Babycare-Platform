from unittest.mock import patch, MagicMock
from datetime import datetime
import pytest
from app.modules.vaccination.service import VaccinationService, _add_months
from app.modules.vaccination.schemas import VaccinationUpdate, VaccinationResponse
from app.shared.exceptions import PermissionDeniedError

def test_add_months_calculation():
    # 0 months
    date_0 = datetime(2026, 1, 10)
    assert _add_months(date_0, 0).strftime("%Y-%m-%d") == "2026-01-10"
    
    # 2 months
    date_2 = datetime(2026, 1, 10)
    assert _add_months(date_2, 2).strftime("%Y-%m-%d") == "2026-03-10"
    
    # 12.5 months (12 months + 15 days)
    # Jan 10 2026 + 12 months = Jan 10 2027
    # Jan 10 2027 + 15 days = Jan 25 2027
    date_12_5 = datetime(2026, 1, 10)
    assert _add_months(date_12_5, 12.5).strftime("%Y-%m-%d") == "2027-01-25"
    
    # Xử lý tràn ngày cuối tháng: ví dụ ngày 31 tháng 1 + 1 tháng = ngày 28 tháng 2
    date_overflow = datetime(2026, 1, 31)
    assert _add_months(date_overflow, 1).strftime("%Y-%m-%d") == "2026-02-28"

@patch("app.modules.vaccination.service.get_firestore_db")
@patch("app.modules.vaccination.service.VaccinationRepository")
def test_generate_default_schedule(mock_repo_cls, mock_get_db):
    mock_repo = mock_repo_cls.return_value
    
    # Giả lập database
    mock_db = MagicMock()
    mock_get_db.return_value = mock_db
    
    vaccine_docs = [
        MagicMock(id="BCG", to_dict=lambda: {"name": "Lao", "recommended_age_months": 0}),
        MagicMock(id="DPT-1", to_dict=lambda: {"name": "5-in-1 Mũi 1", "recommended_age_months": 2}),
    ]
    mock_db.collection.return_value.stream.return_value = vaccine_docs
    
    service = VaccinationService(baby_service=MagicMock())
    service.generate_default_schedule(baby_id="baby123", birth_date_str="2026-01-10")
    
    # Kiểm tra xem phương thức create được gọi đúng 2 lần ứng với 2 vaccine
    assert mock_repo.create.call_count == 2
    
    # Kiểm tra xem ngày tính toán dự kiến có chính xác không
    calls = mock_repo.create.call_args_list
    # Mũi BCG (0 tháng)
    args_bcg, kwargs_bcg = calls[0]
    assert args_bcg[0].vaccine_code == "BCG"
    assert args_bcg[0].scheduled_date == "2026-01-10"
    assert kwargs_bcg.get("doc_id") == "BCG"
    
    # Mũi DPT-1 (2 tháng)
    args_dpt, kwargs_dpt = calls[1]
    assert args_dpt[0].vaccine_code == "DPT-1"
    assert args_dpt[0].scheduled_date == "2026-03-10"
    assert kwargs_dpt.get("doc_id") == "DPT-1"

def test_update_vaccination_permission_denied():
    mock_baby_service = MagicMock()
    # Giả lập lỗi Permission Denied
    mock_baby_service.get_baby_by_id.side_effect = PermissionDeniedError("Denied")
    
    service = VaccinationService(baby_service=mock_baby_service)
    update_data = VaccinationUpdate(status="completed", notes="done")
    
    with pytest.raises(PermissionDeniedError):
        service.update_vaccination_status(
            baby_id="baby123",
            vaccine_code="BCG",
            data_in=update_data,
            user_id="intruder_id"
        )
