from __future__ import annotations
"""SQLite-backed session store — Phase 1.

Survives backend restarts. Swap by setting config.yaml: session.storage = "sqlite"
Schema mirrors memory_store.py exactly so both backends are interchangeable.
"""

import json
from datetime import datetime, timezone

import aiosqlite

from .base import BaseSessionStore
from models.responses import SessionMeta, SessionResults
from core.exceptions import SessionNotFoundError
from core.logging import get_logger

logger = get_logger(__name__)

_CREATE_SESSIONS = """
CREATE TABLE IF NOT EXISTS sessions (
    session_id      TEXT PRIMARY KEY,
    student_name    TEXT NOT NULL,
    session_label   TEXT,
    created_at      TEXT NOT NULL,
    topics_covered  TEXT NOT NULL,   -- JSON array
    questions       TEXT NOT NULL,   -- JSON array
    summary         TEXT NOT NULL,   -- JSON object
    concept_map     TEXT NOT NULL,   -- JSON object
    mcq_score_pct   REAL,
    overall_verdict TEXT
);
"""

_CREATE_RESULTS = """
CREATE TABLE IF NOT EXISTS results (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id  TEXT NOT NULL REFERENCES sessions(session_id),
    result_type TEXT NOT NULL,   -- "mcq" | "voice"
    question_id INTEGER NOT NULL,
    result_data TEXT NOT NULL,   -- JSON object
    UNIQUE (session_id, result_type, question_id)
);
"""


class SQLiteSessionStore(BaseSessionStore):
    """SQLite-backed session store — Phase 1."""

    def __init__(self, db_path: str):
        self._db_path = db_path

    async def _init_db(self, db: aiosqlite.Connection) -> None:
        await db.execute("PRAGMA journal_mode=WAL;")
        await db.execute(_CREATE_SESSIONS)
        await db.execute(_CREATE_RESULTS)
        await db.commit()

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
        now = datetime.now(timezone.utc)
        async with aiosqlite.connect(self._db_path) as db:
            await self._init_db(db)
            await db.execute(
                """INSERT OR IGNORE INTO sessions
                   (session_id, student_name, session_label, created_at,
                    topics_covered, questions, summary, concept_map)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    session_id,
                    student_name,
                    session_label,
                    now.isoformat(),
                    json.dumps(topics_covered),
                    json.dumps(questions),
                    json.dumps(summary),
                    json.dumps(concept_map),
                ),
            )
            await db.commit()
        logger.info("Session saved to SQLite", session_id=session_id, student=student_name)
        return SessionMeta(
            session_id=session_id,
            student_name=student_name,
            session_label=session_label,
            created_at=now,
            topics_covered=topics_covered,
        )

    async def get_session(self, session_id: str) -> dict | None:
        async with aiosqlite.connect(self._db_path) as db:
            await self._init_db(db)
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM sessions WHERE session_id = ?", (session_id,)
            ) as cur:
                row = await cur.fetchone()
            if row is None:
                return None

            session = {
                "session_id": row["session_id"],
                "student_name": row["student_name"],
                "session_label": row["session_label"],
                "created_at": datetime.fromisoformat(row["created_at"]),
                "topics_covered": json.loads(row["topics_covered"]),
                "questions": json.loads(row["questions"]),
                "summary": json.loads(row["summary"]),
                "concept_map": json.loads(row["concept_map"]),
                "mcq_score_pct": row["mcq_score_pct"],
                "overall_verdict": row["overall_verdict"],
                "mcq_results": {},
                "voice_results": {},
            }

            async with db.execute(
                "SELECT result_type, question_id, result_data FROM results WHERE session_id = ?",
                (session_id,),
            ) as cur:
                async for r in cur:
                    key = "mcq_results" if r["result_type"] == "mcq" else "voice_results"
                    session[key][r["question_id"]] = json.loads(r["result_data"])

        return session

    async def list_sessions(self) -> list[SessionMeta]:
        async with aiosqlite.connect(self._db_path) as db:
            await self._init_db(db)
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """SELECT session_id, student_name, session_label, created_at,
                          topics_covered, mcq_score_pct, overall_verdict
                   FROM sessions ORDER BY created_at DESC"""
            ) as cur:
                rows = await cur.fetchall()

        return [
            SessionMeta(
                session_id=r["session_id"],
                student_name=r["student_name"],
                session_label=r["session_label"],
                created_at=datetime.fromisoformat(r["created_at"]),
                topics_covered=json.loads(r["topics_covered"]),
                mcq_score_pct=r["mcq_score_pct"],
                overall_verdict=r["overall_verdict"],
            )
            for r in rows
        ]

    async def update_results(
        self,
        session_id: str,
        result_type: str,
        question_id: int,
        result_data: dict,
    ) -> None:
        async with aiosqlite.connect(self._db_path) as db:
            await self._init_db(db)
            async with db.execute(
                "SELECT session_id FROM sessions WHERE session_id = ?", (session_id,)
            ) as cur:
                if await cur.fetchone() is None:
                    raise SessionNotFoundError(session_id)

            await db.execute(
                """INSERT INTO results (session_id, result_type, question_id, result_data)
                   VALUES (?, ?, ?, ?)
                   ON CONFLICT(session_id, result_type, question_id)
                   DO UPDATE SET result_data = excluded.result_data""",
                (session_id, result_type, question_id, json.dumps(result_data)),
            )
            await db.commit()
            await self._refresh_aggregates(db, session_id)
            await db.commit()

    async def _refresh_aggregates(self, db: aiosqlite.Connection, session_id: str) -> None:
        """Recompute mcq_score_pct and overall_verdict after each result update."""
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT questions FROM sessions WHERE session_id = ?", (session_id,)
        ) as cur:
            row = await cur.fetchone()
        if row is None:
            return

        questions = json.loads(row["questions"])
        mcq_questions = [q for q in questions if q.get("type") == "mcq"]

        async with db.execute(
            "SELECT result_type, question_id, result_data FROM results WHERE session_id = ?",
            (session_id,),
        ) as cur:
            all_results = await cur.fetchall()

        mcq_results = {
            r["question_id"]: json.loads(r["result_data"])
            for r in all_results
            if r["result_type"] == "mcq"
        }
        voice_results = {
            r["question_id"]: json.loads(r["result_data"])
            for r in all_results
            if r["result_type"] == "voice"
        }

        mcq_score_pct = None
        if mcq_questions and mcq_results:
            correct = sum(1 for r in mcq_results.values() if r.get("is_correct"))
            mcq_score_pct = round(correct / len(mcq_questions) * 100, 1)

        overall_verdict = None
        if voice_results:
            latest = list(voice_results.values())[-1]
            overall_verdict = latest.get("verdict")

        await db.execute(
            "UPDATE sessions SET mcq_score_pct = ?, overall_verdict = ? WHERE session_id = ?",
            (mcq_score_pct, overall_verdict, session_id),
        )

    async def compute_session_results(self, session_id: str) -> SessionResults | None:
        session = await self.get_session(session_id)
        if session is None:
            return None

        questions = session.get("questions", [])
        mcq_results_raw = session.get("mcq_results", {})
        voice_results_raw = session.get("voice_results", {})

        mcq_questions = [q for q in questions if q.get("type") == "mcq"]
        voice_questions = [q for q in questions if q.get("type") == "teach_it_back"]

        mcq_results = []
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

        voice_results = []
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
                topic_scores[topic]["avg_voice"] = voice_results_raw[qid].get("weighted_score", 0)

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
