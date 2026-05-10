from __future__ import annotations
"""LLM provider factory.

The single point where config.llm.provider is mapped to a concrete implementation.
Adding a new provider: create one file + add one elif here.
"""

from core.config import AppConfig
from .base import BaseLLMProvider


def create_llm_provider(config: AppConfig) -> BaseLLMProvider:
    """Return the configured LLM provider implementation."""
    # Import inside function to avoid loading unused SDKs at startup
    provider = config.llm.provider.lower()

    if provider in ("ollama", "lmstudio", "openai"):
        from .openai_compatible import OpenAICompatibleProvider
        return OpenAICompatibleProvider(config)
    elif provider == "anthropic":
        from .anthropic_provider import AnthropicProvider
        return AnthropicProvider(config)
    elif provider == "gemini":
        from .gemini_provider import GeminiProvider
        return GeminiProvider(config)
    elif provider == "langchain":
        from .langchain_provider import LangChainProvider
        return LangChainProvider(config)
    else:
        raise ValueError(
            f"Unknown LLM provider '{provider}'. "
            "Valid: ollama | lmstudio | openai | anthropic | gemini | langchain"
        )
