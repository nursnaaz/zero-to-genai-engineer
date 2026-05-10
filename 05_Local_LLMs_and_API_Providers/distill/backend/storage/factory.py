from __future__ import annotations
"""Session store factory."""

from core.config import AppConfig
from .base import BaseSessionStore


def create_session_store(config: AppConfig) -> BaseSessionStore:
    """Return the configured session store backend."""
    storage = config.session.storage.lower()
    if storage == "memory":
        from .memory_store import MemorySessionStore
        return MemorySessionStore(max_sessions=config.session.max_sessions_in_memory)
    elif storage == "sqlite":
        from .sqlite_store import SQLiteSessionStore
        return SQLiteSessionStore(db_path=config.session.sqlite_path)
    else:
        raise ValueError(
            f"Unknown session storage '{storage}'. Valid: memory | sqlite"
        )
