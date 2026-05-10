from __future__ import annotations
"""OpenAI-compatible provider: handles Ollama, LM Studio, and OpenAI.

All three expose the same /v1/chat/completions endpoint format, so a single
client implementation covers all of them.
"""

import os
import httpx
from openai import AsyncOpenAI

from .base import BaseLLMProvider, LLMMessage, LLMResponse
from core.config import AppConfig


class OpenAICompatibleProvider(BaseLLMProvider):
    """
    Provider-agnostic wrapper for any OpenAI-compatible endpoint.

    Routing logic:
    - ollama:   base_url=http://localhost:11434/v1, api_key="ollama" (any string)
    - lmstudio: base_url=http://localhost:1234/v1,  api_key="lm-studio"
    - openai:   base_url=https://api.openai.com/v1, api_key=real key from env

    Uses stream=True internally for local providers (Ollama/LM Studio) so that
    tokens flow continuously over the connection. Local servers enforce a
    per-request idle timeout (~120 s); streaming keeps the socket active and
    eliminates that timeout regardless of how long generation takes.
    """

    def __init__(self, config: AppConfig):
        self._config = config
        provider = config.llm.provider.lower()

        if provider == "ollama":
            base_url = config.llm.ollama.base_url.rstrip("/") + "/v1"
            api_key = "ollama"
            self._use_streaming = True
        elif provider == "lmstudio":
            base_url = config.llm.lmstudio.base_url
            api_key = config.llm.lmstudio.api_key
            self._use_streaming = True   # LM Studio has a 120 s idle timeout
        elif provider == "openai":
            base_url = config.llm.openai.base_url
            api_key = (
                config.llm.api_key
                or os.environ.get("OPENAI_API_KEY", "")
            )
            self._use_streaming = False  # OpenAI cloud has no idle timeout issue
        else:
            raise ValueError(
                f"OpenAICompatibleProvider cannot handle provider '{provider}'. "
                "Expected: ollama | lmstudio | openai"
            )

        # No client-side read timeout: local servers can be slow and we handle
        # progress visibility through SSE; we never want the Python client to
        # cancel a running inference.
        self._client = AsyncOpenAI(
            base_url=base_url,
            api_key=api_key,
            timeout=httpx.Timeout(connect=10.0, read=None, write=None, pool=None),
        )
        self._model = config.llm.model
        self._provider = provider

    async def complete(
        self,
        messages: list[LLMMessage],
        temperature: float | None = None,
        max_tokens: int | None = None,
        response_format: dict | None = None,
    ) -> LLMResponse:
        kwargs: dict = {
            "model": self._model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature if temperature is not None else self._config.llm.temperature,
            "max_tokens": max_tokens if max_tokens is not None else self._config.llm.max_tokens,
        }
        if response_format:
            kwargs["response_format"] = response_format

        if self._use_streaming:
            # Stream tokens so the TCP connection carries data continuously.
            # LM Studio/Ollama close idle connections after ~120 s; streaming
            # bypasses that limit because bytes arrive with every token.
            content_parts: list[str] = []
            prompt_tokens = None
            completion_tokens = None
            model_id = self._model

            stream = await self._client.chat.completions.create(**kwargs, stream=True)
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    content_parts.append(chunk.choices[0].delta.content)
                if chunk.model:
                    model_id = chunk.model
                # Grab usage from the final chunk (some providers include it there)
                if hasattr(chunk, "usage") and chunk.usage:
                    prompt_tokens = chunk.usage.prompt_tokens
                    completion_tokens = chunk.usage.completion_tokens

            return LLMResponse(
                content="".join(content_parts),
                model=model_id,
                provider=self._provider,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
            )

        # Non-streaming path (OpenAI cloud)
        resp = await self._client.chat.completions.create(**kwargs)
        return LLMResponse(
            content=resp.choices[0].message.content or "",
            model=resp.model,
            provider=self._provider,
            prompt_tokens=resp.usage.prompt_tokens if resp.usage else None,
            completion_tokens=resp.usage.completion_tokens if resp.usage else None,
        )

    def get_provider_name(self) -> str:
        return self._provider

    def get_model_name(self) -> str:
        return self._model
