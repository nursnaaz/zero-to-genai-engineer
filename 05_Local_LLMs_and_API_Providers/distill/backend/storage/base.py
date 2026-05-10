from __future__ import annotations
"""Abstract base for session storage backends."""

from abc import ABC, abstractmethod
from datetime import datetime
from models.responses import SessionMeta, SessionResults


class BaseSessionStore(ABC):
    """Storage interface for session data.

    Phase 0: memory_store.py (in-memory dict, no persistence)
    Phase 1: sqlite_store.py (SQLite, survives restarts)
    Phase 2+: postgresql_store.py (multi-tenant production)

    Swapping backends = change config.yaml session.storage, no code changes.
    """

    @abstractmethod
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
        """Create a new session record. Returns the created SessionMeta."""

    @abstractmethod
    async def get_session(self, session_id: str) -> dict | None:
        """Return full session dict or None if not found."""

    @abstractmethod
    async def list_sessions(self) -> list[SessionMeta]:
        """Return all sessions as SessionMeta (newest first)."""

    @abstractmethod
    async def update_results(
        self,
        session_id: str,
        result_type: str,       # "mcq" | "voice"
        question_id: int,
        result_data: dict,
    ) -> None:
        """Append an MCQ or voice evaluation result to a session."""

    @abstractmethod
    async def compute_session_results(self, session_id: str) -> SessionResults | None:
        """Compute aggregated results from stored per-question data."""
