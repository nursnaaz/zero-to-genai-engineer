from __future__ import annotations
"""POST /api/analyze — main entry point for transcript analysis."""

import uuid
from fastapi import APIRouter, Request, HTTPException
from models.requests import AnalyzeRequest
from models.responses import AnalyzeResponse
from core.exceptions import DistillError
from core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(body: AnalyzeRequest, request: Request) -> AnalyzeResponse:
    """
    Analyze a classroom transcript:
    1. Run TranscriptAnalyzer → summary + concept map
    2. Run QuestionGenerator → MCQ + teach-it-back questions
    3. Store session → return AnalyzeResponse

    This is the slowest endpoint (LLM calls). Typical time: 15–90s depending on model.
    """
    analyzer = request.app.state.analyzer
    assessor = request.app.state.assessor
    store = request.app.state.store

    session_id = str(uuid.uuid4())
    transcript = body.transcript

    logger.info(
        "Analyze request",
        session_id=session_id,
        student=body.student_name,
        transcript_chars=len(transcript),
    )

    try:
        # Step 1: Analyze transcript → summary + concept map
        summary, concept_map = await analyzer.analyze(transcript)

        # Step 2: Generate questions from summary
        summary_dict = summary.model_dump()
        questions = await assessor.generate(summary_dict, transcript)
        questions_dicts = [q.model_dump() for q in questions]
    except DistillError:
        raise  # let the registered distill_exception_handler return structured JSON

    try:
        # Step 3: Persist session (separate try so storage failures give a distinct 503)
        await store.save_session(
            session_id=session_id,
            student_name=body.student_name,
            session_label=body.session_label,
            topics_covered=summary.topics_covered,
            questions=questions_dicts,
            summary=summary_dict,
            concept_map=concept_map.model_dump(),
        )
    except Exception as exc:
        logger.error("Session storage failed", session_id=session_id, error=str(exc))
        raise HTTPException(status_code=503, detail="Session storage unavailable. Please retry.") from exc

    logger.info(
        "Analysis complete",
        session_id=session_id,
        questions=len(questions),
        topics=len(summary.topics_covered),
    )

    return AnalyzeResponse(
        session_id=session_id,
        summary=summary,
        questions=questions,
        concept_map=concept_map,
    )
