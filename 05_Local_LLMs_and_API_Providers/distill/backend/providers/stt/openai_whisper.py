from __future__ import annotations
"""OpenAI Whisper API STT provider."""

import io
import os
from openai import AsyncOpenAI

from .base import BaseSTTProvider
from core.config import AppConfig


class OpenAIWhisperProvider(BaseSTTProvider):
    """Transcribes audio using the OpenAI Whisper API (cloud)."""

    def __init__(self, config: AppConfig):
        self._config = config
        api_key = os.environ.get("OPENAI_API_KEY") or config.llm.api_key or ""
        self._client = AsyncOpenAI(api_key=api_key)
        self._model = config.speech_to_text.openai_whisper.model

    async def transcribe(self, audio_bytes: bytes, filename: str) -> dict:
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = filename

        resp = await self._client.audio.transcriptions.create(
            model=self._model,
            file=audio_file,
            language=self._config.speech_to_text.language or None,
        )
        return {
            "transcript": resp.text.strip(),
            "duration_seconds": None,
            "language": self._config.speech_to_text.language,
        }

    def get_provider_name(self) -> str:
        return "openai_whisper"
