import os
import pytest
from unittest.mock import patch
from app.AI_agents.llmops.observability.tracing import (
    LangSmithTracerManager,
    get_tracer_callbacks
)


def test_langsmith_tracer_manager_disabled():
    """Verify tracer returns None when LANGCHAIN_TRACING_V2 is not 'true'."""
    LangSmithTracerManager.clear()
    with patch.dict(os.environ, {"LANGCHAIN_TRACING_V2": "false"}):
        tracer = LangSmithTracerManager.get_tracer()
        assert tracer is None
        callbacks = get_tracer_callbacks()
        assert callbacks == []


def test_langsmith_tracer_manager_enabled():
    """Verify tracer returns callback instance when LANGCHAIN_TRACING_V2 is 'true'."""
    LangSmithTracerManager.clear()
    with patch.dict(os.environ, {
        "LANGCHAIN_TRACING_V2": "true",
        "LANGCHAIN_PROJECT": "test-babycare-project"
    }):
        callbacks = get_tracer_callbacks()
        assert len(callbacks) == 1
        assert callbacks[0] is not None
