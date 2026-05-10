from __future__ import annotations
"""Unit tests for LLM and STT providers (using mock implementations)."""

import pytest
from providers.llm.base import LLMMessage, LLMResponse, BaseLLMProvider
from providers.llm.factory import create_llm_provider
from providers.stt.base import BaseSTTProvider
from providers.stt.factory import create_stt_provider
from core.exceptions import ProviderError
from .conftest import MockLLMProvider, MockSTTProvider, make_test_config


@pytest.mark.asyncio
async def test_mock_llm_returns_content():
    llm = MockLLMProvider(response_content="Hello from mock")
    msgs = [LLMMessage(role="user", content="Say hello")]
    resp = await llm.complete(msgs)
    assert resp.content == "Hello from mock"
    assert resp.provider == "mock"
    assert llm.call_count == 1


@pytest.mark.asyncio
async def test_mock_llm_tracks_messages():
    llm = MockLLMProvider()
    msgs = [
        LLMMessage(role="system", content="You are helpful"),
        LLMMessage(role="user", content="Test"),
    ]
    await llm.complete(msgs)
    assert len(llm.last_messages) == 2
    assert llm.last_messages[0].role == "system"


def test_llm_factory_ollama(test_config):
    """Factory should return an OpenAICompatibleProvider for ollama."""
    from providers.llm.openai_compatible import OpenAICompatibleProvider
    provider = create_llm_provider(test_config)
    assert isinstance(provider, OpenAICompatibleProvider)
    assert provider.get_provider_name() == "ollama"


def test_llm_factory_invalid_provider(test_config):
    """Factory should raise ValueError for unknown provider."""
    test_config.llm.provider = "nonexistent_provider"
    with pytest.raises(ValueError, match="Unknown LLM provider"):
        create_llm_provider(test_config)


def test_stt_factory_whisper_local(test_config):
    """Factory should return WhisperLocalProvider for whisper_local config."""
    # Don't actually download the model in tests
    test_config.speech_to_text.whisper_local.download_on_startup = False
    from providers.stt.whisper_local import WhisperLocalProvider
    provider = create_stt_provider(test_config)
    assert isinstance(provider, WhisperLocalProvider)
    assert provider.get_provider_name() == "whisper_local"


def test_stt_factory_invalid_provider(test_config):
    test_config.speech_to_text.provider = "nonexistent_stt"
    with pytest.raises(ValueError, match="Unknown STT provider"):
        create_stt_provider(test_config)


@pytest.mark.asyncio
async def test_mock_stt_transcription():
    stt = MockSTTProvider()
    result = await stt.transcribe(b"fake audio bytes", "test.webm")
    assert "transcript" in result
    assert len(result["transcript"]) > 0
    assert result["language"] == "en"
