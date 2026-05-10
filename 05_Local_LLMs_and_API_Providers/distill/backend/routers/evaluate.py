from __future__ import annotations
"""POST /api/evaluate/mcq and /api/evaluate/voice."""

from fastapi import APIRouter, Request, HTTPException
from models.requests import MCQEvaluateRequest, VoiceEvaluateRequest
from models.responses import MCQEvaluationResponse, VoiceEvaluationResponse
from core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post("/evaluate/mcq", response_model=MCQEvaluationResponse)
async def evaluate_mcq(body: MCQEvaluateRequest, request: Request) -> MCQEvaluationResponse:
    """Evaluate a student's MCQ answer.

    - Correctness is determined server-side (not trusted from client)
    - LLM adds explanation and optional hint
    - Updates session record and adaptive difficulty
    """
    store = request.app.state.store
    evaluator = request.app.state.evaluator

    # Load session
    session = await store.get_session(body.session_id)
    if session is None:
        raise HTTPException(status_code=404, detail=f"Session '{body.session_id}' not found.")

    # Find the question
    questions = session.get("questions", [])
    question = next((q for q in questions if q["id"] == body.question_id), None)
    if question is None:
        raise HTTPException(status_code=404, detail=f"Question {body.question_id} not found in session.")

    # Evaluate
    result = await evaluator.evaluate_mcq(
        question=question,
        selected_answer=body.selected_answer,
        hint_level=body.hint_level_used,
    )

    # Persist result
    await store.update_results(
        session_id=body.session_id,
        result_type="mcq",
        question_id=body.question_id,
        result_data={
            "selected_answer": body.selected_answer,
            "is_correct": result.is_correct,
            "correct_answer": result.correct_answer,
            "explanation": result.explanation,
            "next_difficulty": result.next_difficulty,
        },
    )

    logger.info(
        "MCQ evaluated",
        session_id=body.session_id,
        question_id=body.question_id,
        is_correct=result.is_correct,
    )
    return result


@router.post("/evaluate/voice", response_model=VoiceEvaluationResponse)
async def evaluate_voice(body: VoiceEvaluateRequest, request: Request) -> VoiceEvaluationResponse:
    """Evaluate a student's teach-it-back voice/text answer.

    Runs the full LLM interview evaluation (5 dimensions + narrative debrief).
    """
    store = request.app.state.store
    evaluator = request.app.state.evaluator

    # Load session
    session = await store.get_session(body.session_id)
    if session is None:
        raise HTTPException(status_code=404, detail=f"Session '{body.session_id}' not found.")

    # Find the question
    questions = session.get("questions", [])
    question = next((q for q in questions if q["id"] == body.question_id), None)
    if question is None:
        raise HTTPException(status_code=404, detail=f"Question {body.question_id} not found in session.")

    # Build session context for the evaluator (summary of what was taught)
    summary = session.get("summary", {})
    session_context = (
        f"Session: {summary.get('session_title', '')}\n"
        f"Topics: {', '.join(summary.get('topics_covered', []))}\n"
        f"Teacher insight: {summary.get('teacher_insight', '')}"
    )

    result = await evaluator.evaluate_voice(
        question=question,
        student_answer=body.student_answer,
        session_context=session_context,
        was_voice=body.was_voice,
    )

    # Persist result
    await store.update_results(
        session_id=body.session_id,
        result_type="voice",
        question_id=body.question_id,
        result_data={
            "student_answer": body.student_answer,
            "dimension_scores": [d.model_dump() for d in result.dimension_scores],
            "weighted_score": result.weighted_score,
            "verdict": result.verdict,
            "verdict_type": result.verdict_type,
            "narrative_debrief": result.narrative_debrief,
        },
    )

    logger.info(
        "Voice evaluated",
        session_id=body.session_id,
        question_id=body.question_id,
        weighted_score=result.weighted_score,
        verdict=result.verdict,
    )
    return result
