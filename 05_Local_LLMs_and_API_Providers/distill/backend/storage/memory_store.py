from __future__ import annotations
"""In-memory session store for Phase 0 (local demo).

Stores sessions in a Python dict. Data is lost on server restart.
Capped at config.session.max_sessions_in_memory (evicts oldest when full).
Thread-safe via asyncio.Lock.
"""

import asyncio
import uuid
from collections import OrderedDict
from datetime import datetime, timezone

from .base import BaseSessionStore
from models.responses import SessionMeta, SessionResults
from core.exceptions import SessionNotFoundError
from core.logging import get_logger

logger = get_logger(__name__)


class MemorySessionStore(BaseSessionStore):
    """In-memory session store — Phase 0 only."""

    def __init__(self, max_sessions: int = 100):
        self._max = max_sessions
        # OrderedDict for O(1) insertion-order eviction (oldest first)
        self._sessions: OrderedDict[str, dict] = OrderedDict()
        self._lock = asyncio.Lock()

    async def save_session(
        self,
        session_id: str,
        student_name: str,
        session_label: str | None,
        topics_covered: list[str],
        questions: list[dict],
        summary: dict,
        concept_map: dict,
    ) -> SessionMeta:
        async with self._lock:
            if len(self._sessions) >= self._max:
                # Evict the oldest session to stay within memory cap
                evicted_id, _ = self._sessions.popitem(last=False)
                logger.warning("Evicted oldest session from memory", evicted_id=evicted_id)

            now = datetime.now(timezone.utc)
            self._sessions[session_id] = {
                "session_id": session_id,
                "student_name": student_name,
                "session_label": session_label,
                "created_at": now,
                "topics_covered": topics_covered,
                "questions": questions,      # list of Question dicts
                "summary": summary,          # SummaryResponse dict
                "concept_map": concept_map,  # ConceptMapResponse dict
                "mcq_results": {},           # {question_id: result_dict}
                "voice_results": {},         # {question_id: result_dict}
            }
            logger.info("Session saved", session_id=session_id, student=student_name)
            return SessionMeta(
                session_id=session_id,
                student_name=student_name,
                session_label=session_label,
                created_at=now,
                topics_covered=topics_covered,
            )

    async def get_session(self, session_id: str) -> dict | None:
        async with self._lock:
            return self._sessions.get(session_id)

    async def list_sessions(self) -> list[SessionMeta]:
        async with self._lock:
            result = []
            for s in reversed(self._sessions.values()):  # newest first
                result.append(
                    SessionMeta(
                        session_id=s["session_id"],
                        student_name=s["student_name"],
                        session_label=s.get("session_label"),
                        created_at=s["created_at"],
                        topics_covered=s.get("topics_covered", []),
                        mcq_score_pct=s.get("mcq_score_pct"),
                        overall_verdict=s.get("overall_verdict"),
                    )
                )
            return result

    async def update_results(
        self,
        session_id: str,
        result_type: str,
        question_id: int,
        result_data: dict,
    ) -> None:
        async with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                raise SessionNotFoundError(session_id)
            key = "mcq_results" if result_type == "mcq" else "voice_results"
            session[key][question_id] = result_data
            # Update cached aggregate stats for sidebar display
            self._update_aggregates(session)

    def _update_aggregates(self, session: dict) -> None:
        """Update mcq_score_pct and overall_verdict after each answer."""
        mcq = session["mcq_results"]
        voice = session["voice_results"]

        # MCQ score
        questions = session.get("questions", [])
        mcq_questions = [q for q in questions if q.get("type") == "mcq"]
        if mcq_questions and mcq:
            correct = sum(1 for r in mcq.values() if r.get("is_correct"))
            session["mcq_score_pct"] = round(correct / len(mcq_questions) * 100, 1)

        # Overall verdict (from latest voice evaluation)
        if voice:
            latest_voice = list(voice.values())[-1]
            session["overall_verdict"] = latest_voice.get("verdict")

    async def compute_session_results(self, session_id: str) -> SessionResults | None:
        async with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                return None

            questions = session.get("questions", [])
            mcq_results_raw = session.get("mcq_results", {})
            voice_results_raw = session.get("voice_results", {})

            # Build MCQ result list
            mcq_results = []
            mcq_questions = [q for q in questions if q.get("type") == "mcq"]
            for q in mcq_questions:
                qid = q["id"]
                if qid in mcq_results_raw:
                    r = mcq_results_raw[qid]
                    mcq_results.append({
                        "question_id": qid,
                        "selected": r.get("selected_answer"),
                        "is_correct": r.get("is_correct"),
                        "correct_answer": r.get("correct_answer"),
                        "explanation": r.get("explanation", ""),
                    })

            # Build voice result list
            voice_results = []
            voice_questions = [q for q in questions if q.get("type") == "teach_it_back"]
            for q in voice_questions:
                qid = q["id"]
                if qid in voice_results_raw:
                    r = voice_results_raw[qid]
                    voice_results.append({
                        "question_id": qid,
                        "student_answer": r.get("student_answer", ""),
                        "dimension_scores": r.get("dimension_scores", []),
                        "weighted_score": r.get("weighted_score", 0),
                        "verdict": r.get("verdict", ""),
                    })

            # Per-topic aggregation
            topic_scores: dict[str, dict] = {}
            for q in mcq_questions:
                topic = q.get("topic", "General")
                qid = q["id"]
                if topic not in topic_scores:
                    topic_scores[topic] = {"correct": 0, "total": 0}
                topic_scores[topic]["total"] += 1
                if mcq_results_raw.get(qid, {}).get("is_correct"):
                    topic_scores[topic]["correct"] += 1

            for q in voice_questions:
                topic = q.get("topic", "General")
                qid = q["id"]
                if topic not in topic_scores:
                    topic_scores[topic] = {"correct": 0, "total": 0}
                if qid in voice_results_raw:
                    existing = topic_scores[topic]
                    voice_score = voice_results_raw[qid].get("weighted_score", 0)
                    existing["avg_voice"] = voice_score

            # Compute overall scores
            overall_mcq = session.get("mcq_score_pct", 0.0) or 0.0
            voice_scores = [r.get("weighted_score", 0) for r in voice_results_raw.values()]
            overall_voice = round(sum(voice_scores) / len(voice_scores), 2) if voice_scores else 0.0

            return SessionResults(
                mcq_results=mcq_results,
                voice_results=voice_results,
                topic_scores=topic_scores,
                overall_mcq_pct=overall_mcq,
                overall_voice_score=overall_voice,
            )
