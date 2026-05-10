from __future__ import annotations
"""Anthropic Claude provider for Distill."""

import os
import anthropic

from .base import BaseLLMProvider, LLMMessage, LLMResponse
from core.config import AppConfig


class AnthropicProvider(BaseLLMProvider):
    """Wraps the Anthropic SDK (claude-3-* models)."""

    def __init__(self, config: AppConfig):
        self._config = config
        api_key = (
            config.llm.api_key
            or os.environ.get("ANTHROPIC_API_KEY", "")
        )
        self._client = anthropic.AsyncAnthropic(api_key=api_key)
        self._model = config.llm.model

    async def complete(
        self,
        messages: list[LLMMessage],
        temperature: float | None = None,
        max_tokens: int | None = None,
        response_format: dict | None = None,
    ) -> LLMResponse:
        # Anthropic separates system prompt from conversation messages
        system_content = ""
        chat_messages = []
        for m in messages:
            if m.role == "system":
                system_content = m.content
            else:
                chat_messages.append({"role": m.role, "content": m.content})

        kwargs: dict = {
            "model": self._model,
            "max_tokens": max_tokens if max_tokens is not None else self._config.llm.max_tokens,
            "messages": chat_messages,
        }
        if system_content:
            kwargs["system"] = system_content
        if temperature is not None:
            kwargs["temperature"] = temperature

        resp = await self._client.messages.create(**kwargs)
        content = resp.content[0].text if resp.content else ""
        return LLMResponse(
            content=content,
            model=resp.model,
            provider="anthropic",
            prompt_tokens=resp.usage.input_tokens if resp.usage else None,
            completion_tokens=resp.usage.output_tokens if resp.usage else None,
        )

    def get_provider_name(self) -> str:
        return "anthropic"

    def get_model_name(self) -> str:
        return self._model
