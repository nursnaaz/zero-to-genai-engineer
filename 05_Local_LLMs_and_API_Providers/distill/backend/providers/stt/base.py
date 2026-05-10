from __future__ import annotations
"""Base abstraction for all Speech-to-Text providers."""

from abc import ABC, abstractmethod


class BaseSTTProvider(ABC):
    """All STT providers implement this interface."""

    @abstractmethod
    async def transcribe(self, audio_bytes: bytes, filename: str) -> dict:
        """Transcribe audio bytes to text.

        Args:
            audio_bytes: Raw audio file content (webm/wav/mp4).
            filename: Original filename (used to infer format).

        Returns:
            dict with keys:
                transcript (str): The transcribed text.
                duration_seconds (float | None): Audio duration.
                language (str | None): Detected language code.
        """

    @abstractmethod
    def get_provider_name(self) -> str:
        """Return the STT provider identifier."""
