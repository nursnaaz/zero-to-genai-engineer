from __future__ import annotations
"""Integration tests for API endpoints using FastAPI TestClient."""

import asyncio
import json
import pytest
from fastapi.testclient import TestClient

from .conftest import MockLLMProvider, MockSTTProvider, make_test_config


SAMPLE_ANALYZE_RESULT = {
    "session_id": "test-session-123",
    "summary": {
        "session_title": "RAG Basics",
        "topics_covered": ["RAG"],
        "key_concepts": [{"concept": "RAG", "explanation": "Retrieval Augmented Generation", "topic": "RAG"}],
        "learning_objectives": ["Understand RAG"],
        "teacher_insight": "Teacher focused on practical examples.",
        "confusion_zones": [],
    },
    "questions": [
        {
            "id": 1, "type": "mcq", "topic": "RAG", "difficulty": "medium",
            "bloom_level": "understand", "question": "What is RAG?",
            "options": [
                {"key": "A", "text": "Retrieval Augmented Generation"},
                {"key": "B", "text": "Wrong"}, {"key": "C", "text": "Wrong"}, {"key": "D", "text": "Wrong"},
            ],
            "correct_answer": "A", "explanation": "RAG = Retrieval Augmented Generation.",
        }
    ],
    "concept_map": {"mermaid_syntax": 'graph TD\n    A["RAG"] --> B["Retrieval"]', "nodes": ["RAG"], "edges": []},
}


def make_app_with_mocks(analyze_json_str: str | None = None):
    """Create a test FastAPI app with all dependencies mocked."""
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from main import create_app
    from core.prompt_manager import PromptManager
    from services.analyzer import TranscriptAnalyzer
    from services.assessor import QuestionGenerator
    from services.evaluator import AnswerEvaluator
    from storage.memory_store import MemorySessionStore

    config = make_test_config()
    app = create_app()
    prompt_mgr = PromptManager(config)
    mock_llm = MockLLMProvider(response_content=analyze_json_str or json.dumps(SAMPLE_ANALYZE_RESULT))
    mock_stt = MockSTTProvider()
    store = MemorySessionStore(max_sessions=10)

    app.state.config = config
    app.state.llm = mock_llm
    app.state.stt = mock_stt
    app.state.store = store
    app.state.analyzer = TranscriptAnalyzer(mock_llm, prompt_mgr, config)
    app.state.assessor = QuestionGenerator(mock_llm, prompt_mgr, config)
    app.state.evaluator = AnswerEvaluator(mock_llm, prompt_mgr, config)

    return TestClient(app, raise_server_exceptions=False), store, mock_llm


def _seed_session(store, session_id: str = "test-sess") -> None:
    """Seed a session directly into the in-memory store (sync wrapper)."""
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(
            store.save_session(
                session_id=session_id,
                student_name="Test Student",
                session_label=None,
                topics_covered=["RAG"],
                questions=[{
                    "id": 1, "type": "mcq", "topic": "RAG", "difficulty": "medium",
                    "question": "What is RAG?", "correct_answer": "A",
                    "options": [
                        {"key": "A", "text": "Right"},
                        {"key": "B", "text": "Wrong"},
                        {"key": "C", "text": "Wrong"},
                        {"key": "D", "text": "Wrong"},
                    ],
                }],
                summary={
                    "session_title": "RAG", "topics_covered": ["RAG"],
                    "key_concepts": [], "learning_objectives": [],
                    "teacher_insight": "", "confusion_zones": [],
                },
                concept_map={"mermaid_syntax": "", "nodes": [], "edges": []},
            )
        )
    finally:
        loop.close()


def test_health_endpoint():
    client, _, _ = make_app_with_mocks()
    resp = client.get("/api/health")
    # Health endpoint tests LLM with a live call — with mock it returns degraded or ok
    assert resp.status_code == 200
    data = resp.json()
    assert data["llm_provider"] == "mock"
    assert data["stt_provider"] == "mock_stt"
    assert data["version"] == "0.1.0"
    assert data["status"] in ("ok", "degraded")


def test_ui_config_endpoint():
    client, _, _ = make_app_with_mocks()
    resp = client.get("/api/config/ui")
    assert resp.status_code == 200
    data = resp.json()
    assert data["brand_name"] == "Distill"
    assert "mcq_count" in data["assessment_config"]


def test_sessions_list_empty():
    client, _, _ = make_app_with_mocks()
    resp = client.get("/api/sessions")
    assert resp.status_code == 200
    assert resp.json()["sessions"] == []


def test_session_not_found():
    client, _, _ = make_app_with_mocks()
    resp = client.get("/api/session/nonexistent-id")
    assert resp.status_code == 404


def test_mcq_evaluate_session_not_found():
    client, _, _ = make_app_with_mocks()
    resp = client.post("/api/evaluate/mcq", json={
        "session_id": "nonexistent",
        "question_id": 1,
        "selected_answer": "A",
    })
    assert resp.status_code == 404


def test_evaluate_mcq_correct_answer():
    """MCQ evaluation: correct answer returns is_correct=True and next_difficulty."""
    client, store, mock_llm = make_app_with_mocks()

    # Seed a session directly into the store
    _seed_session(store, "test-sess")

    # Mock LLM returns a valid MCQ eval JSON
    mock_llm.set_response(json.dumps({
        "is_correct": True,
        "explanation": "A is correct.",
        "next_difficulty": "hard",
        "hint": None,
    }))

    resp = client.post("/api/evaluate/mcq", json={
        "session_id": "test-sess",
        "question_id": 1,
        "selected_answer": "A",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_correct"] is True   # server-side check, not LLM
    assert data["next_difficulty"] in ("easy", "medium", "hard")
