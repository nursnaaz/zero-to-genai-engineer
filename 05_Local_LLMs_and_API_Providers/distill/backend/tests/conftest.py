from __future__ import annotations
"""Shared pytest fixtures for all Distill backend tests."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient

from core.config import AppConfig, LLMConfig, STTConfig, AssessmentConfig, EvaluationConfig
from core.config import InterviewerConfig, ScoreDimensionConfig, VerdictConfig, EvalOutputConfig
from core.config import MCQConfig, TeachItBackConfig, BloomConfig, AdaptiveEngineConfig
from core.config import ConceptMapConfig, SessionConfig, PromptsConfig, ExportConfig, ServerConfig
from providers.llm.base import BaseLLMProvider, LLMMessage, LLMResponse
from providers.stt.base import BaseSTTProvider
from storage.memory_store import MemorySessionStore


def make_test_config() -> AppConfig:
    """Build a minimal AppConfig for tests — no real providers, no files needed."""
    cfg = AppConfig()
    cfg.app_name = "Distill Test"
    cfg.version = "0.1.0"
    cfg.brand_name = "Distill"
    cfg.brand_tagline = "Pure knowledge, every class"
    cfg.log_level = "WARNING"

    cfg.llm.provider = "ollama"
    cfg.llm.model = "gemma3:9b"
    cfg.llm.temperature = 0.3
    cfg.llm.max_tokens = 4000
    cfg.llm.retry_attempts = 1  # only 1 retry in tests for speed
    cfg.llm.retry_delay_seconds = 0

    cfg.assessment.mcq.count = 3
    cfg.assessment.teach_it_back.count = 1

    cfg.evaluation.interviewer = InterviewerConfig(
        name="Dr. Priya",
        persona="Test persona.",
        style="Structured",
        domain="AI",
    )
    cfg.evaluation.score_dimensions = [
        ScoreDimensionConfig(key="accuracy", label="Accuracy", weight=0.5, description=""),
        ScoreDimensionConfig(key="clarity", label="Clarity", weight=0.5, description=""),
    ]
    cfg.evaluation.verdicts = [
        VerdictConfig(label="Strong", min_weighted_score=4.0, cloudscape_type="success"),
        VerdictConfig(label="Developing", min_weighted_score=0.0, cloudscape_type="warning"),
    ]
    cfg.evaluation.output = EvalOutputConfig(max_recommendations=3)

    cfg.session.storage = "memory"
    cfg.session.max_sessions_in_memory = 10

    cfg.prompts.directory = "./prompts"
    cfg.concept_map.direction = "TD"
    cfg.concept_map.max_nodes = 20

    return cfg


class MockLLMProvider(BaseLLMProvider):
    """Mock LLM provider for unit tests. Returns canned responses."""

    def __init__(self, response_content: str = '{"result": "ok"}'):
        self._response = response_content
        self.call_count = 0
        self.last_messages: list[LLMMessage] = []

    def set_response(self, content: str) -> None:
        self._response = content

    async def complete(self, messages, temperature=None, max_tokens=None, response_format=None) -> LLMResponse:
        self.call_count += 1
        self.last_messages = messages
        return LLMResponse(
            content=self._response,
            model="mock-model",
            provider="mock",
            prompt_tokens=10,
            completion_tokens=20,
        )

    def get_provider_name(self) -> str:
        return "mock"

    def get_model_name(self) -> str:
        return "mock-model"


class MockSTTProvider(BaseSTTProvider):
    """Mock STT provider for unit tests."""

    async def transcribe(self, audio_bytes: bytes, filename: str) -> dict:
        return {
            "transcript": "This is a test transcription of the audio.",
            "duration_seconds": 5.0,
            "language": "en",
        }

    def get_provider_name(self) -> str:
        return "mock_stt"


@pytest.fixture
def test_config() -> AppConfig:
    return make_test_config()


@pytest.fixture
def mock_llm() -> MockLLMProvider:
    return MockLLMProvider()


@pytest.fixture
def mock_stt() -> MockSTTProvider:
    return MockSTTProvider()


@pytest.fixture
def memory_store() -> MemorySessionStore:
    return MemorySessionStore(max_sessions=10)


@pytest.fixture
def test_client(test_config, mock_llm, mock_stt, memory_store):
    """FastAPI TestClient with all dependencies mocked."""
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

    from main import create_app
    from core.prompt_manager import PromptManager
    from services.analyzer import TranscriptAnalyzer
    from services.assessor import QuestionGenerator
    from services.evaluator import AnswerEvaluator

    app = create_app()

    # Override lifespan by setting state directly
    prompt_mgr = PromptManager(test_config)
    app.state.config = test_config
    app.state.llm = mock_llm
    app.state.stt = mock_stt
    app.state.store = memory_store
    app.state.analyzer = TranscriptAnalyzer(mock_llm, prompt_mgr, test_config)
    app.state.assessor = QuestionGenerator(mock_llm, prompt_mgr, test_config)
    app.state.evaluator = AnswerEvaluator(mock_llm, prompt_mgr, test_config)

    return TestClient(app, raise_server_exceptions=False)
