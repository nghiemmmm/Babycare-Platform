import pytest
from app.AI_agents.llmops.observability.logging import (
    ToolStepLogger,
    AgentExecutionLogger
)


def test_tool_step_logger_create_and_append():
    """Verify ToolStepLogger creates structured dictionary and appends to state."""
    state = {}
    step = ToolStepLogger.create_step(
        tool_name="MedicalRetriever",
        display_name="Tra cứu tài liệu y tế WHO",
        args={"query": "sốt 38.5C"},
        result_summary="Tìm thấy 2 tài liệu",
        duration_ms=45,
        status="completed"
    )

    assert isinstance(step, dict)
    assert step["tool_name"] == "MedicalRetriever"
    assert step["display_name"] == "Tra cứu tài liệu y tế WHO"
    assert step["args"]["query"] == "sốt 38.5C"
    assert step["duration_ms"] == 45
    assert step["status"] == "completed"
    assert "id" in step
    assert "start_time" in step

    ToolStepLogger.append_step(state, step)
    assert "tool_steps" in state
    assert len(state["tool_steps"]) == 1
    assert state["tool_steps"][0]["tool_name"] == "MedicalRetriever"


def test_agent_execution_logger(caplog):
    """Verify AgentExecutionLogger logs start, step, complete, error without exception."""
    with caplog.at_level("INFO"):
        AgentExecutionLogger.log_start(run_id="run_1", trace_id="trace_1", agent_name="ChatAgent", query="Bé mấy tháng lẫy?")
        assert "Nhận yêu cầu" in caplog.text

        step = ToolStepLogger.create_step(tool_name="GrowthTool", display_name="Đọc chỉ số tăng trưởng", duration_ms=20)
        AgentExecutionLogger.log_step(run_id="run_1", trace_id="trace_1", step=step)
        assert "Thực thi: 'Đọc chỉ số tăng trưởng'" in caplog.text

        AgentExecutionLogger.log_complete(run_id="run_1", trace_id="trace_1", duration_ms=150)
        assert "Hoàn thành xử lý" in caplog.text

        AgentExecutionLogger.log_error(run_id="run_1", trace_id="trace_1", error=RuntimeError("Test error"))
        assert "Lỗi xử lý" in caplog.text
