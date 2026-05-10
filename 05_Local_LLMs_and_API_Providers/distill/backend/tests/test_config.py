from __future__ import annotations
"""Tests for core/config.py."""

import pytest
from core.config import load_config, get_config, AppConfig
from pathlib import Path


def test_load_config_defaults():
    """load_config with no file should return default AppConfig."""
    cfg = load_config(config_path=Path("/nonexistent/path.yaml"))
    assert isinstance(cfg, AppConfig)
    assert cfg.app_name == "Distill"
    assert cfg.llm.provider == "ollama"
    assert cfg.llm.model == "gemma3:9b"


def test_get_config_returns_singleton():
    """get_config() should return the same object on repeated calls."""
    cfg1 = get_config()
    cfg2 = get_config()
    assert cfg1 is cfg2


def test_config_assessment_defaults():
    cfg = load_config(config_path=Path("/nonexistent/path.yaml"))
    assert cfg.assessment.mcq.count == 5
    assert cfg.assessment.teach_it_back.count == 3
    assert cfg.assessment.bloom_taxonomy.enabled is True


def test_config_evaluation_defaults():
    # Interviewer name has a dataclass default; score_dimensions/verdicts are
    # defined only in config.yaml (not dataclass defaults), so load the real file.
    cfg_defaults = load_config(config_path=Path("/nonexistent/path.yaml"))
    assert cfg_defaults.evaluation.interviewer.name == "Dr. Priya"

    # Load from the real config.yaml for assertions about list-valued settings
    real_config = Path(__file__).parent.parent.parent / "config.yaml"
    if real_config.exists():
        cfg = load_config(config_path=real_config)
        assert len(cfg.evaluation.score_dimensions) == 5
        assert len(cfg.evaluation.verdicts) == 4


def test_config_server_defaults():
    cfg = load_config(config_path=Path("/nonexistent/path.yaml"))
    assert cfg.server.port == 8000
    assert "http://localhost:5173" in cfg.server.cors_origins
