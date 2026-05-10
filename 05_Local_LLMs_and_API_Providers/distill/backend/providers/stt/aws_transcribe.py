from __future__ import annotations
"""AWS Transcribe STT provider — Phase 2 stub."""

from .base import BaseSTTProvider
from core.config import AppConfig
from core.exceptions import TranscriptionError


class AWSTranscribeProvider(BaseSTTProvider):
    """AWS Transcribe STT provider.

    TODO (Phase 2): Implement using boto3. Steps:
    1. Upload audio_bytes to config.speech_to_text.aws_transcribe.s3_bucket
    2. Start transcription job with start_transcription_job()
    3. Poll until job status is COMPLETED
    4. Fetch and parse the transcript JSON from S3
    5. Return transcript text + duration

    Requires: boto3, AWS credentials in env vars (AWS_ACCESS_KEY_ID, etc.)
    """

    def __init__(self, config: AppConfig):
        self._config = config

    async def transcribe(self, audio_bytes: bytes, filename: str) -> dict:
        raise TranscriptionError(
            "AWS Transcribe is not yet implemented (Phase 2).",
            hint="Switch to whisper_local or openai_whisper in config.yaml.",
        )

    def get_provider_name(self) -> str:
        return "aws_transcribe"
