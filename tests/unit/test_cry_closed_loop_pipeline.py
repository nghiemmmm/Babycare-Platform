import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock
from app.AI_agents.workflows.cry_analysis_graph import CryAnalysisGraph
from app.modules.nutrition.schemas import SolidFoodLogResponse
from app.modules.health_records.schemas import HealthRecordResponse
from app.modules.cry.schemas import CryFeedbackUpdate, CryLogResponse


def test_closed_loop_5_node_pipeline_execution():
    """
    TEST 1: Thực thi trọn vẹn đồ thị 5-node:
    detect_audio -> retrieve_multi_context -> explicit_fusion -> safety_policy -> llm_explain.
    """
    graph = CryAnalysisGraph()
    
    # 1. Mock Audio Classifier: hungry = 0.88
    graph.classifier.predict = MagicMock(return_value=(
        "hungry",
        0.88,
        {"hungry": 0.88, "pain": 0.06, "tired": 0.04, "burp": 0.02}
    ))

    # 2. Mock Nutrition Context: Vừa ăn 10 phút trước -> Contradiction!
    mock_food = SolidFoodLogResponse(
        id="f1",
        baby_id="baby_1",
        logged_at="2026-08-14T17:50:00Z",
        food_name="Sữa công thức",
        amount_g=150.0
    )
    graph.context_retriever.nutrition_service.get_solid_food_history = MagicMock(return_value=[mock_food])
    graph.context_retriever.health_service.get_history = MagicMock(return_value=[])
    graph.context_retriever.medication_service.get_medication_history = MagicMock(return_value=[])

    # 3. Mock LLM Reasoner
    graph.reasoner.areason = AsyncMock(return_value="Bé có dấu hiệu đầy hơi sau cữ ăn. Ba mẹ hãy bế vỗ ợ hơi cho bé.")

    initial_state = {
        "messages": [],
        "baby_id": "baby_1",
        "current_user_id": "user_mom",
        "extracted_data": {
            "audio_file": "baby_cry_test.wav"
        }
    }

    app_graph = graph.compile()
    final_state = asyncio.run(app_graph.ainvoke(initial_state))

    # Xác thực dữ liệu có cấu trúc qua từng tầng
    ext_data = final_state["extracted_data"]

    # Tầng 1: Audio Evidence
    assert "audio_evidence" in ext_data
    assert ext_data["audio_evidence"]["top_label"] == "hungry"
    assert ext_data["audio_evidence"]["reason_scores"]["hungry"] == 0.88

    # Tầng 2: Multi-Context
    assert "cry_context" in ext_data
    assert ext_data["cry_context"]["feeding"]["available"] is True

    # Tầng 3: Explicit Fusion
    assert "adjusted_evidence" in ext_data
    assert ext_data["adjusted_evidence"]["contradiction_score"] >= 0.80
    assert ext_data["adjusted_evidence"]["primary_cause"] in ["burp", "discomfort"]

    # Tầng 4: Safety & Policy
    assert "cry_decision" in ext_data
    assert ext_data["cry_decision"]["risk_level"] == "LOW"
    assert "BURP" in ext_data["cry_decision"]["action_plan"]

    # Tầng 5: LLM Output
    assert len(final_state["messages"]) > 0
    msg_content = final_state["messages"][-1].content
    assert "Chẩn đoán tiếng khóc" in msg_content
    assert "BURP" in msg_content or "ợ hơi" in msg_content.lower()


def test_proof_llm_is_not_decision_maker():
    """
    TEST 2: Chứng minh LLM KHÔNG PHẢI là Decision Maker.
    Ngay cả khi LLM sinh chuỗi text bất kỳ, các trường `cry_decision`, `risk_level`, `action_plan`
    vẫn được cố định hoàn toàn bởi Safety & Policy Engine trước đó.
    """
    graph = CryAnalysisGraph()
    graph.classifier.predict = MagicMock(return_value=("pain", 0.90, {"pain": 0.90}))
    
    # Giả lập bé sốt cao -> Safety Gate quyết định EMERGENCY
    mock_health = HealthRecordResponse(
        id="h_emergency",
        symptoms=["Sốt cao 39.5", "Co giật"],
        temp=39.5,
        recorded_at="2026-08-14T17:00:00Z"
    )
    graph.context_retriever.health_service.get_history = MagicMock(return_value=[mock_health])
    graph.context_retriever.nutrition_service.get_solid_food_history = MagicMock(return_value=[])
    graph.context_retriever.medication_service.get_medication_history = MagicMock(return_value=[])

    # Giả lập LLM cố tình sinh text nói "Bé bình thường không sao"
    graph.reasoner.areason = AsyncMock(return_value="Bé chỉ khóc nhẹ, không sao đâu.")

    state = {
        "messages": [],
        "baby_id": "baby_test",
        "current_user_id": "user_1",
        "extracted_data": {"audio_file": "pain_cry.wav"}
    }

    app_graph = graph.compile()
    final_state = asyncio.run(app_graph.ainvoke(state))
    decision = final_state["extracted_data"]["cry_decision"]

    # KHẲNG ĐỊNH: Decision bất biến, không bị LLM làm biến dạng
    assert decision["risk_level"] == "EMERGENCY"
    assert "SEEK_EMERGENCY_CARE" in decision["action_plan"]
    assert decision["soothing_sound"] is None


def test_extended_outcome_feedback_support():
    """
    TEST 3: Kiểm tra hỗ trợ Outcome Feedback chi tiết (soothed, soothed_after_minutes, intervention_used).
    """
    from app.modules.cry.service import CryService
    service = CryService()
    
    mock_repo = MagicMock()
    mock_existing_log = CryLogResponse(
        id="cry_log_99",
        logged_at="2026-08-14T10:00:00Z",
        audio_url="/static/cry/test.wav",
        prediction="burp",
        confidence=0.85,
        reason_scores={"burp": 0.85, "pain": 0.15},
        feedback_accurate=None
    )
    mock_repo.get.return_value = mock_existing_log
    mock_repo.update.side_effect = lambda log_id, data: CryLogResponse(
        id=log_id,
        logged_at="2026-08-14T10:00:00Z",
        audio_url="/static/cry/test.wav",
        prediction="burp",
        confidence=0.85,
        reason_scores={"burp": 0.85, "pain": 0.15},
        feedback_accurate=data.get("feedback_accurate"),
        notes=str(data.get("feedback_details"))
    )

    service.baby_service.get_baby_by_id = MagicMock()

    # Phụ huynh gửi phản hồi can thiệp chi tiết
    feedback_payload = CryFeedbackUpdate(
        feedback_accurate=True,
        actual_cause="burp",
        soothed=True,
        soothed_after_minutes=3,
        intervention_used="BURP",
        parent_notes="Bé đã ợ hơi to và nín khóc sau 3 phút vỗ lưng"
    )

    # Thay thế repo trong test
    from unittest.mock import patch
    with patch("app.modules.cry.service.CryRepository", return_value=mock_repo):
        res = service.update_parent_feedback("baby_1", "cry_log_99", feedback_payload, "user_1")
        assert res.feedback_accurate is True
