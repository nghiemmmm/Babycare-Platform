import pytest
from app.AI_agents.llmops.model_registry import ModelRegistry, LLMModelInfo, ModelVersions


def test_model_registry_registration_and_retrieval():
    """Verify ModelRegistry registers and retrieves LLM model specs."""
    info = ModelRegistry.get_info("gemini-2.0-flash")
    assert info is not None
    assert info.provider == "google"
    assert info.context_window == 1000000

    models = ModelRegistry.list_models()
    assert len(models) >= 3


def test_model_versions_aliases():
    """Verify ModelVersions resolves model aliases correctly."""
    assert ModelVersions.get_model_by_alias("fast") == ModelVersions.FAST_LITE
    assert ModelVersions.get_model_by_alias("default") == ModelVersions.DEFAULT_FLASH
    assert ModelVersions.get_model_by_alias("high") == ModelVersions.HIGH_PRO
    assert ModelVersions.get_model_by_alias("unknown") == ModelVersions.DEFAULT_FLASH

    ModelVersions.register_alias("experimental", "gemini-3.0-pro")
    assert ModelVersions.get_model_by_alias("experimental") == "gemini-3.0-pro"
