from __future__ import annotations
"""POST /api/transcribe — audio file → transcript text."""

from fastapi import APIRouter, Request, UploadFile, File, HTTPException
from models.responses import TranscribeResponse
from core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe(
    request: Request,
    audio: UploadFile = File(..., description="Audio file (webm/wav/mp4)"),
) -> TranscribeResponse:
    """Transcribe an audio recording using the configured STT provider.

    Accepts WebM (from MediaRecorder), WAV, or MP4 audio.
    Returns the transcript text for display and editing before submission.
    """
    stt = request.app.state.stt
    config = request.app.state.config

    # Size guard
    max_bytes = config.server.max_upload_size_mb * 1024 * 1024
    audio_bytes = await audio.read()
    if len(audio_bytes) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"Audio file too large. Max size: {config.server.max_upload_size_mb}MB",
        )

    filename = audio.filename or "recording.webm"
    logger.info("Transcribe request", filename=filename, size_kb=len(audio_bytes) // 1024)

    result = await stt.transcribe(audio_bytes, filename)

    return TranscribeResponse(
        transcript=result.get("transcript", ""),
        duration_seconds=result.get("duration_seconds"),
        language_detected=result.get("language"),
    )
