from __future__ import annotations
"""Custom exceptions and FastAPI error handlers for Distill."""

from fastapi import Request
from fastapi.responses import JSONResponse


class DistillError(Exception):
    """Base exception. All Distill-specific errors inherit from this."""
    http_status: int = 400  # subclasses override this to set the correct HTTP status

    def __init__(self, message: str, code: str = "DISTILL_ERROR", hint: str = ""):
        super().__init__(message)
        self.code = code
        self.hint = hint


class ProviderError(DistillError):
    """Raised when an LLM or STT provider fails."""
    def __init__(self, message: str, provider: str = "", hint: str = ""):
        super().__init__(
            message,
            code="PROVIDER_ERROR",
            hint=hint or f"Check that the {provider} provider is running and configured correctly.",
        )
        self.provider = provider


class TranscriptionError(DistillError):
    """Raised when audio transcription fails."""
    def __init__(self, message: str, hint: str = ""):
        super().__init__(
            message,
            code="TRANSCRIPTION_ERROR",
            hint=hint or "Check audio file format (webm/wav/mp4) and size.",
        )


class EvaluationError(DistillError):
    """Raised when AI evaluation fails (e.g. invalid JSON response)."""
    def __init__(self, message: str, hint: str = ""):
        super().__init__(
            message,
            code="EVALUATION_ERROR",
            hint=hint or "The LLM returned an unexpected response. Try again.",
        )


class SessionNotFoundError(DistillError):
    """Raised when a session_id doesn't exist in the store."""
    http_status: int = 404

    def __init__(self, session_id: str):
        super().__init__(
            f"Session '{session_id}' not found.",
            code="SESSION_NOT_FOUND",
            hint="The session may have expired. Start a new assessment.",
        )


class ConfigError(DistillError):
    """Raised for invalid configuration."""
    def __init__(self, message: str):
        super().__init__(message, code="CONFIG_ERROR", hint="Check config.yaml for the invalid setting.")


# ── FastAPI exception handlers ─────────────────────────────────────────────────

async def distill_exception_handler(request: Request, exc: DistillError) -> JSONResponse:
    """Convert DistillError subclasses into structured JSON error responses."""
    return JSONResponse(
        status_code=exc.http_status,
        content={
            "detail": str(exc),
            "code": exc.code,
            "hint": exc.hint,
        },
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all: never expose raw tracebacks to the student."""
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An unexpected error occurred. Please try again.",
            "code": "INTERNAL_ERROR",
            "hint": "Check the server logs for details.",
        },
    )
