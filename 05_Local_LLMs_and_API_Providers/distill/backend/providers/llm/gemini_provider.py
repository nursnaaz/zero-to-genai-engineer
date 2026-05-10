from __future__ import annotations
"""Google Gemini provider for Distill."""

import os
import google.generativeai as genai

from .base import BaseLLMProvider, LLMMessage, LLMResponse
from core.config import AppConfig


class GeminiProvider(BaseLLMProvider):
    """Wraps the google-generativeai SDK."""

    def __init__(self, config: AppConfig):
        self._config = config
        api_key = (
            config.llm.api_key
            or os.environ.get("GOOGLE_API_KEY", "")
        )
        genai.configure(api_key=api_key)
        self._model_name = config.llm.model
        self._model = genai.GenerativeModel(self._model_name)

    async def complete(
        self,
        messages: list[LLMMessage],
        temperature: float | None = None,
        max_tokens: int | None = None,
        response_format: dict | None = None,
    ) -> LLMResponse:
        # Build Gemini-compatible history (system → user context, then conversation)
        system_parts: list[str] = []
        history: list[dict] = []
        last_user_message = ""

        for m in messages:
            if m.role == "system":
                system_parts.append(m.content)
            elif m.role == "user":
                last_user_message = m.content
                if history and history[-1]["role"] == "model":
                    history.append({"role": "user", "parts": [m.content]})
                elif history:
                    history.append({"role": "user", "parts": [m.content]})
                else:
                    history.append({"role": "user", "parts": [m.content]})
            elif m.role == "assistant":
                history.append({"role": "model", "parts": [m.content]})

        # Prepend system prompt as first user turn if present
        if system_parts and history:
            system_text = "\n\n".join(system_parts)
            # Inject system context into the first user message
            first_user = history[0]["parts"][0]
            history[0]["parts"][0] = f"{system_text}\n\n{first_user}"

        gen_config = genai.GenerationConfig(
            temperature=temperature if temperature is not None else self._config.llm.temperature,
            max_output_tokens=max_tokens if max_tokens is not None else self._config.llm.max_tokens,
        )

        # Use the last message as the current prompt, rest as history
        prompt = history[-1]["parts"][0] if history else last_user_message
        chat_history = history[:-1] if len(history) > 1 else []

        chat = self._model.start_chat(history=chat_history)
        resp = await chat.send_message_async(prompt, generation_config=gen_config)

        content = resp.text or ""
        return LLMResponse(
            content=content,
            model=self._model_name,
            provider="gemini",
        )

    def get_provider_name(self) -> str:
        return "gemini"

    def get_model_name(self) -> str:
        return self._model_name
