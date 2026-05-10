from __future__ import annotations
"""Unit tests for analyzer, assessor, and evaluator services."""

import json
import pytest
from services.analyzer import TranscriptAnalyzer, _extract_json
from services.assessor import QuestionGenerator
from services.evaluator import AnswerEvaluator
from core.prompt_manager import PromptManager
from providers.llm.base import LLMMessage, LLMResponse
from .conftest import MockLLMProvider, make_test_config


SAMPLE_SUMMARY_JSON = json.dumps({
    "session_title": "Introduction to RAG",
    "topics_covered": ["RAG basics", "Vector databases"],
    "key_concepts": [
        {"concept": "Retrieval", "explanation": "Finding relevant docs.", "topic": "RAG basics"},
        {"concept": "ChromaDB", "explanation": "A vector store.", "topic": "Vector databases"},
    ],
    "learning_objectives": ["Understand RAG pipeline"],
    "teacher_insight": "Teacher focused on practical implementation.",
    "confusion_zones": [
        {
            "topic": "RAG basics",
            "signal_type": "student_question",
            "description": "Students confused about chunking",
            "timestamp_approx": None,
        }
    ],
})

SAMPLE_MERMAID = """graph TD
    A["RAG"] --> B["Retrieval"]
    A --> C["Generation"]
    B --> D["ChromaDB"]"""

SAMPLE_QUESTIONS_JSON = json.dumps({
    "questions": [
        {
            "id": 1,
            "type": "mcq",
            "topic": "RAG basics",
            "difficulty": "medium",
            "bloom_level": "understand",
            "question": "What does RAG stand for?",
            "options": [
                {"key": "A", "text": "Retrieval Augmented Generation"},
                {"key": "B", "text": "Random Answer Generation"},
                {"key": "C", "text": "Recursive Algorithm Graph"},
                {"key": "D", "text": "Real AI Generation"},
            ],
            "correct_answer": "A",
            "explanation": "RAG = Retrieval Augmented Generation.",
        },
        {
            "id": 2,
            "type": "teach_it_back",
            "topic": "Vector databases",
            "difficulty": "medium",
            "bloom_level": "understand",
            "question": "Explain how ChromaDB stores vectors.",
            "evaluation_rubric": "Should include: purpose, how vectors are indexed, similarity search.",
        },
    ]
})

SAMPLE_MCQ_EVAL_JSON = json.dumps({
    "is_correct": True,
    "explanation": "RAG stands for Retrieval Augmented Generation.",
    "next_difficulty": "hard",
    "hint": None,
})

SAMPLE_VOICE_EVAL_JSON = json.dumps({
    "dimension_scores": [
        {"key": "accuracy", "label": "Accuracy", "score": 4, "weight": 0.5},
        {"key": "clarity", "label": "Clarity", "score": 3, "weight": 0.5},
    ],
    "narrative_debrief": "Para 1: Good job.\n\nPara 2: Missing details.\n\nPara 3: Study more.",
    "verdict": "Good — minor gaps to address",
    "follow_up_question": "Can you explain the chunking strategy?",
    "study_recommendations": ["Read ChromaDB docs", "Practice with examples", "Review embeddings"],
})


@pytest.fixture
def test_config():
    return make_test_config()


@pytest.fixture
def prompt_mgr(test_config):
    return PromptManager(test_config)


@pytest.mark.asyncio
async def test_analyzer_returns_summary_and_map(test_config, prompt_mgr):
    """Analyzer should parse LLM JSON into SummaryResponse + ConceptMapResponse."""
    # The analyzer makes two calls:
    #   call 1 → summary JSON
    #   call 2 → mermaid syntax (returned directly, not JSON-parsed)
    call_count = [0]

    class TwoCallMockLLM(MockLLMProvider):
        async def complete(self, messages, temperature=None, max_tokens=None, response_format=None):
            call_count[0] += 1
            content = SAMPLE_SUMMARY_JSON if call_count[0] == 1 else SAMPLE_MERMAID
            self.call_count += 1
            self.last_messages = messages
            return LLMResponse(
                content=content,
                model="mock-model",
                provider="mock",
                prompt_tokens=10,
                completion_tokens=20,
            )

    llm = TwoCallMockLLM()
    analyzer = TranscriptAnalyzer(llm, prompt_mgr, test_config)

    summary, concept_map = await analyzer.analyze("This is a long transcript about RAG " * 20)

    assert summary.session_title == "Introduction to RAG"
    assert "RAG basics" in summary.topics_covered
    assert len(summary.key_concepts) == 2
    assert "graph TD" in concept_map.mermaid_syntax


@pytest.mark.asyncio
async def test_assessor_returns_questions(test_config, prompt_mgr):
    """Assessor should parse questions JSON into list of Question models."""
    llm = MockLLMProvider(response_content=SAMPLE_QUESTIONS_JSON)
    assessor = QuestionGenerator(llm, prompt_mgr, test_config)

    summary_dict = json.loads(SAMPLE_SUMMARY_JSON)
    questions = await assessor.generate(summary_dict, "test transcript")

    assert len(questions) == 2
    mcq = next(q for q in questions if q.type == "mcq")
    tib = next(q for q in questions if q.type == "teach_it_back")
    assert mcq.correct_answer == "A"
    assert len(mcq.options) == 4
    assert tib.evaluation_rubric is not None


@pytest.mark.asyncio
async def test_evaluator_mcq_correct(test_config, prompt_mgr):
    """MCQ evaluator: is_correct determined server-side (not from LLM)."""
    llm = MockLLMProvider(response_content=SAMPLE_MCQ_EVAL_JSON)
    evaluator = AnswerEvaluator(llm, prompt_mgr, test_config)

    question = {
        "id": 1, "type": "mcq", "question": "What does RAG stand for?",
        "difficulty": "medium", "correct_answer": "A",
        "options": [
            {"key": "A", "text": "Retrieval Augmented Generation"},
            {"key": "B", "text": "Wrong"},
            {"key": "C", "text": "Wrong"},
            {"key": "D", "text": "Wrong"},
        ],
    }
    result = await evaluator.evaluate_mcq(question=question, selected_answer="A")
    assert result.is_correct is True
    assert result.next_difficulty in ("easy", "medium", "hard")


@pytest.mark.asyncio
async def test_evaluator_mcq_wrong_answer(test_config, prompt_mgr):
    """MCQ: is_correct=False when student selects wrong answer, regardless of LLM."""
    llm = MockLLMProvider(response_content=SAMPLE_MCQ_EVAL_JSON)
    evaluator = AnswerEvaluator(llm, prompt_mgr, test_config)

    question = {
        "id": 1, "type": "mcq", "question": "Test?",
        "difficulty": "hard", "correct_answer": "A",
        "options": [{"key": k, "text": "t"} for k in ["A", "B", "C", "D"]],
    }
    result = await evaluator.evaluate_mcq(question=question, selected_answer="B")
    assert result.is_correct is False  # B != A regardless of LLM response


@pytest.mark.asyncio
async def test_evaluator_voice(test_config, prompt_mgr):
    """Voice evaluator should compute weighted score and determine verdict."""
    llm = MockLLMProvider(response_content=SAMPLE_VOICE_EVAL_JSON)
    evaluator = AnswerEvaluator(llm, prompt_mgr, test_config)

    question = {
        "id": 2, "type": "teach_it_back",
        "question": "Explain ChromaDB.",
        "evaluation_rubric": "Include: purpose, how it works, example.",
    }
    result = await evaluator.evaluate_voice(
        question=question,
        student_answer="ChromaDB is a vector database used for storing embeddings.",
        session_context="Session about RAG and vector databases.",
    )
    assert 1.0 <= result.weighted_score <= 5.0
    assert result.narrative_debrief != ""
    assert result.verdict != ""
    assert len(result.dimension_scores) == 2


def test_extract_json_strips_fences():
    """_extract_json should strip markdown code fences."""
    raw = '```json\n{"key": "value"}\n```'
    assert _extract_json(raw) == '{"key": "value"}'


def test_extract_json_plain():
    raw = '{"key": "value"}'
    assert _extract_json(raw) == '{"key": "value"}'
