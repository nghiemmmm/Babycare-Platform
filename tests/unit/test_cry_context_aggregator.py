import pytest
import asyncio
from unittest.mock import MagicMock
from app.AI_agents.workflows.cry_analysis_graph import CryAnalysisGraph
from app.modules.nutrition.schemas import SolidFoodLogResponse


def test_context_aggregator_node_with_feeding_history():
    """
    Test Case 1: Khi bé có nhật ký ăn dặm gần nhất,
    context_aggregator_node phải trích xuất chính xác tên món, lượng ăn và thời gian.
    """
    graph = CryAnalysisGraph()

    # Mock SolidFoodService để trả về 1 bản ghi ăn dặm mẫu
    mock_log = SolidFoodLogResponse(
        id="log_123",
        baby_id="baby_leo",
        logged_at="2026-08-14 16:30:00",
        food_name="Cháo cá hồi bí đỏ",
        amount_g=120,
        reaction="Thích ăn, không dị ứng",
        notes="Ăn hết suất"
    )
    graph.nutrition_service.get_solid_food_history = MagicMock(return_value=[mock_log])

    state = {
        "messages": [],
        "baby_id": "baby_leo",
        "current_user_id": "user_mom_1",
        "extracted_data": {"audio_file": "baby_cry_hungry.wav"}
    }

    result = asyncio.run(graph.context_aggregator_node(state))

    assert "extracted_data" in result
    feeding_history = result["extracted_data"].get("feeding_history")
    
    # Kiểm tra nội dung chuỗi trả về
    assert feeding_history is not None
    assert "Cháo cá hồi bí đỏ" in feeding_history
    assert f"{mock_log.amount_g}g" in feeding_history
    assert "2026-08-14 16:30:00" in feeding_history
    assert feeding_history == f"Ăn dặm gần nhất: Cháo cá hồi bí đỏ lượng {mock_log.amount_g}g vào lúc 2026-08-14 16:30:00"



def test_context_aggregator_node_fallback_when_no_history():
    """
    Test Case 2: Khi chưa có dữ liệu hoặc gặp lỗi kết nối,
    node phải trả về chuỗi fallback an toàn thay vì gây crash.
    """
    graph = CryAnalysisGraph()
    graph.nutrition_service.get_solid_food_history = MagicMock(return_value=[])

    state = {
        "messages": [],
        "baby_id": "baby_newborn",
        "current_user_id": "user_mom_2",
        "extracted_data": {}
    }

    result = asyncio.run(graph.context_aggregator_node(state))

    feeding_history = result["extracted_data"].get("feeding_history")
    assert feeding_history == "chưa có dữ liệu sinh hoạt gần đây."
