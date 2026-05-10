from __future__ import annotations
"""Google Cloud Speech-to-Text STT provider — Phase 2 stub."""

from .base import BaseSTTProvider
from core.config import AppConfig
from core.exceptions import TranscriptionError


class GoogleSTTProvider(BaseSTTProvider):
    """Google Cloud STT provider.

    TODO (Phase 2): Implement using google-cloud-speech:
    1. Load credentials from config.speech_to_text.google_stt.credentials_path
    2. Create SpeechClient
    3. Call recognize() with audio bytes
    4. Return transcript + confidence

    Requires: google-cloud-speech, service account JSON credentials
    """

    def __init__(self, config: AppConfig):
        self._config = config

    async def transcribe(self, audio_bytes: bytes, filename: str) -> dict:
        raise TranscriptionError(
            "Google STT is not yet implemented (Phase 2).",
            hint="Switch to whisper_local or openai_whisper in config.yaml.",
        )

    def get_provider_name(self) -> str:
        return "google_stt"
