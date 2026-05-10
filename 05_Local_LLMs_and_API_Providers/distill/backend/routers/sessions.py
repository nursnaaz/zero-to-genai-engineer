from __future__ import annotations
"""GET /api/sessions and GET /api/session/{session_id}."""

from fastapi import APIRouter, Request, HTTPException
from models.responses import SessionMeta, SessionResults
from core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get("/sessions")
async def list_sessions(request: Request) -> dict:
    """Return session history for the sidebar."""
    store = request.app.state.store
    sessions = await store.list_sessions()
    return {"sessions": [s.model_dump() for s in sessions]}


@router.get("/session/{session_id}")
async def get_session(session_id: str, request: Request) -> dict:
    """Return full session data including computed results."""
    store = request.app.state.store

    session = await store.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")

    meta = SessionMeta(
        session_id=session["session_id"],
        student_name=session["student_name"],
        session_label=session.get("session_label"),
        created_at=session["created_at"],
        topics_covered=session.get("topics_covered", []),
        mcq_score_pct=session.get("mcq_score_pct"),
        overall_verdict=session.get("overall_verdict"),
    )

    results = await store.compute_session_results(session_id)

    return {
        "session": meta.model_dump(),
        "results": results.model_dump() if results else None,
    }
