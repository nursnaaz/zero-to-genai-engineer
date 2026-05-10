from __future__ import annotations
"""POST /api/analyze/stream — SSE endpoint that emits live progress events."""

import asyncio
import json
import uuid
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from models.requests import AnalyzeRequest

router = APIRouter()


@router.post("/analyze/stream")
async def analyze_stream(body: AnalyzeRequest, request: Request) -> StreamingResponse:
    """
    Same pipeline as /api/analyze but streams Server-Sent Events so the
    frontend can show live progress instead of a blank loading spinner.

    Each event: `data: <json>\\n\\n`
    Stages: reading → splitting → chunk → merging → summary →
            concept_map → questions → saving → done | error
    """
    analyzer = request.app.state.analyzer
    assessor = request.app.state.assessor
    store = request.app.state.store

    session_id = str(uuid.uuid4())
    transcript = body.transcript

    queue: asyncio.Queue[dict] = asyncio.Queue()

    async def emit(event: dict) -> None:
        await queue.put(event)

    async def _run() -> None:
        try:
            summary, concept_map = await analyzer.analyze(transcript, emit=emit)
            summary_dict = summary.model_dump()

            questions = await assessor.generate(summary_dict, transcript, emit=emit)
            questions_dicts = [q.model_dump() for q in questions]

            await emit({"stage": "saving", "message": "Saving your session",
                        "detail": "Storing results so you can return any time"})

            await store.save_session(
                session_id=session_id,
                student_name=body.student_name,
                session_label=body.session_label,
                topics_covered=summary.topics_covered,
                questions=questions_dicts,
                summary=summary_dict,
                concept_map=concept_map.model_dump(),
            )

            await emit({
                "stage": "done",
                "result": {
                    "session_id": session_id,
                    "summary": summary_dict,
                    "questions": questions_dicts,
                    "concept_map": concept_map.model_dump(),
                },
            })
        except Exception as exc:
            await emit({"stage": "error", "message": str(exc)})

    task = asyncio.create_task(_run())

    async def _generate():
        try:
            while True:
                # Poll the queue; also check if client disconnected
                if await request.is_disconnected():
                    task.cancel()
                    return
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    # Send a keepalive comment so the connection stays open
                    yield ": keepalive\n\n"
                    continue
                yield f"data: {json.dumps(event)}\n\n"
                if event.get("stage") in ("done", "error"):
                    break
        finally:
            # Ensure the background task finishes cleanly
            if not task.done():
                await asyncio.shield(task)

    return StreamingResponse(
        _generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
