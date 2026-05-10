from __future__ import annotations
"""Local Whisper STT provider using openai-whisper.

Downloads model on first use (size from config). Runs on CPU by default.
Whisper prefers 16kHz mono audio — the frontend MediaRecorder should capture
at { audio: { channelCount: 1, sampleRate: 16000 } }.
"""

import asyncio
import os
import ssl
import tempfile
import time
from pathlib import Path

from .base import BaseSTTProvider
from core.config import AppConfig
from core.logging import get_logger

logger = get_logger(__name__)


class WhisperLocalProvider(BaseSTTProvider):
    """Transcribes audio using a locally-loaded Whisper model."""

    def __init__(self, config: AppConfig):
        self._config = config
        self._model = None  # loaded lazily or on startup

        if config.speech_to_text.whisper_local.download_on_startup:
            self._load_model()

    def _load_model(self) -> None:
        """Load (and optionally download) the Whisper model."""
        import whisper

        # macOS Python 3.10 (python.org build) ships without system CA certs wired in.
        # Point urllib (used by Whisper's downloader) at certifi's bundle so the
        # download doesn't fail with SSLCertVerificationError.
        try:
            import certifi
            os.environ.setdefault("SSL_CERT_FILE", certifi.where())
            os.environ.setdefault("REQUESTS_CA_BUNDLE", certifi.where())
            ssl._create_default_https_context = ssl.create_default_context  # noqa: SLF001
        except ImportError:
            pass  # certifi not installed — carry on and hope system certs work

        model_size = self._config.speech_to_text.whisper_local.model_size
        device = self._config.speech_to_text.whisper_local.device

        logger.info(
            "Loading Whisper model — this may take a minute on first run",
            model=model_size,
            device=device,
        )
        t0 = time.time()
        self._model = whisper.load_model(model_size, device=device)
        logger.info("Whisper model ready", elapsed_seconds=round(time.time() - t0, 1))

    async def transcribe(self, audio_bytes: bytes, filename: str) -> dict:
        """Transcribe audio using local Whisper model."""
        if self._model is None:
            self._load_model()

        # Determine file suffix for temp file
        suffix = Path(filename).suffix or ".webm"

        # Write to temp file (Whisper reads from disk)
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        try:
            # Run blocking Whisper in thread pool to avoid blocking event loop
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self._model.transcribe(  # type: ignore[union-attr]
                    tmp_path,
                    language=self._config.speech_to_text.language or None,
                    fp16=False,  # fp16=False required for CPU
                ),
            )
            return {
                "transcript": result.get("text", "").strip(),
                "duration_seconds": None,  # Whisper doesn't return duration directly
                "language": result.get("language"),
            }
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    def get_provider_name(self) -> str:
        return "whisper_local"
