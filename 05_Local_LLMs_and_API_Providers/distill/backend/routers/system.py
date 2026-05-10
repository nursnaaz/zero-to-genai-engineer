from __future__ import annotations
"""System routers: /api/health and /api/config/ui."""

from fastapi import APIRouter, Request
from models.responses import HealthResponse, UIConfigResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health(request: Request) -> HealthResponse:
    """Health check. Tests LLM provider with a trivial call."""
    llm = request.app.state.llm
    config = request.app.state.config

    # Try a lightweight LLM call to verify the provider is reachable
    status = "ok"
    try:
        from providers.llm.base import LLMMessage
        resp = await llm.complete(
            [LLMMessage(role="user", content="Say 'ok'")],
            max_tokens=10,
            temperature=0.0,
        )
        if not resp.content:
            status = "degraded"
    except Exception:
        status = "degraded"

    return HealthResponse(
        status=status,
        llm_provider=llm.get_provider_name(),
        llm_model=llm.get_model_name(),
        stt_provider=request.app.state.stt.get_provider_name(),
        version=config.version,
    )


@router.get("/config/ui", response_model=UIConfigResponse)
async def ui_config(request: Request) -> UIConfigResponse:
    """Return a safe subset of configuration for the frontend."""
    config = request.app.state.config
    asmt = config.assessment
    return UIConfigResponse(
        brand_name=config.brand_name,
        brand_tagline=config.brand_tagline,
        features=config.ui.get("features", {}),
        assessment_config={
            "mcq_count": asmt.mcq.count,
            "tib_count": asmt.teach_it_back.count,
            "voice_enabled": asmt.teach_it_back.voice_enabled,
            "text_fallback": asmt.teach_it_back.text_fallback,
            "adaptive_enabled": asmt.adaptive_engine.enabled,
            "initial_difficulty": asmt.adaptive_engine.initial_difficulty,
            "hint_levels": asmt.mcq.hint_levels,
            "min_answer_words": asmt.teach_it_back.min_answer_words,
            "max_recording_seconds": asmt.teach_it_back.max_recording_seconds,
        },
    )
