from __future__ import annotations
"""STT provider factory."""

from core.config import AppConfig
from .base import BaseSTTProvider


def create_stt_provider(config: AppConfig) -> BaseSTTProvider:
    """Return the configured STT provider implementation."""
    provider = config.speech_to_text.provider.lower()

    if provider == "whisper_local":
        from .whisper_local import WhisperLocalProvider
        return WhisperLocalProvider(config)
    elif provider == "openai_whisper":
        from .openai_whisper import OpenAIWhisperProvider
        return OpenAIWhisperProvider(config)
    elif provider == "aws_transcribe":
        from .aws_transcribe import AWSTranscribeProvider
        return AWSTranscribeProvider(config)
    elif provider == "google_stt":
        from .google_stt import GoogleSTTProvider
        return GoogleSTTProvider(config)
    else:
        raise ValueError(
            f"Unknown STT provider '{provider}'. "
            "Valid: whisper_local | openai_whisper | aws_transcribe | google_stt"
        )
