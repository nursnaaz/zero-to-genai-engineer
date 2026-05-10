from __future__ import annotations
"""QuestionGenerator service.

Takes the session summary + transcript and generates MCQ + teach-it-back questions.
Uses the questions_system.j2 prompt template.
"""

import json
from typing import Callable, Awaitable, Any
from core.config import AppConfig
from core.exceptions import EvaluationError
from core.logging import get_logger
from core.prompt_manager import PromptManager
from core.utils import extract_json as _extract_json
from providers.llm.base import BaseLLMProvider, LLMMessage
from models.responses import Question, MCQOption

Emit = Callable[[dict[str, Any]], Awaitable[None]]

async def _noop(event: dict[str, Any]) -> None:
    pass

logger = get_logger(__name__)


class QuestionGenerator:
    """Generates a mixed question set from a session summary."""

    def __init__(self, llm: BaseLLMProvider, prompt_mgr: PromptManager, config: AppConfig):
        self._llm = llm
        self._prompt = prompt_mgr
        self._config = config

    async def generate(self, summary_dict: dict, transcript: str, emit: Emit = _noop) -> list[Question]:
        """Generate MCQ + teach-it-back questions for this session."""
        cfg = self._config.assessment
        bloom_cfg = cfg.bloom_taxonomy
        mcq_count = cfg.mcq.count
        tib_count = cfg.teach_it_back.count
        total = mcq_count + tib_count

        confusion_zones = summary_dict.get("confusion_zones", [])

        await emit({
            "stage": "questions",
            "message": f"Generating {total} quiz questions",
            "detail": f"{mcq_count} multiple-choice  ·  {tib_count} Teach-It-Back exercises",
        })

        prompt_text = self._prompt.render(
            "questions",
            topics=summary_dict.get("topics_covered", []),
            session_summary=json.dumps(summary_dict, indent=2),
            confusion_zones=confusion_zones,
            bloom_enabled=bloom_cfg.enabled,
            bloom_distribution=bloom_cfg.distribution,
            total_questions=total,
            mcq_count=mcq_count,
            tib_count=tib_count,
            difficulty_distribution=cfg.mcq.difficulty_distribution,
        )

        messages = [LLMMessage(role="user", content=prompt_text)]

        last_error = None
        resp = None
        for attempt in range(1, self._config.llm.retry_attempts + 1):
            try:
                resp = await self._llm.complete(messages)
                raw = _extract_json(resp.content)
                data = json.loads(raw)
                questions_raw = data.get("questions", [])
                questions = self._parse_questions(questions_raw)
                logger.info(
                    "Questions generated",
                    mcq=len([q for q in questions if q.type == "mcq"]),
                    tib=len([q for q in questions if q.type == "teach_it_back"]),
                )
                return questions
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                last_error = e
                logger.warning("Question parse failed", attempt=attempt, error=str(e))
                if attempt < self._config.llm.retry_attempts:
                    messages = messages + [
                        LLMMessage(role="assistant", content=resp.content if resp is not None else ""),
                        LLMMessage(role="user", content="Return ONLY valid JSON with the questions array."),
                    ]

        raise EvaluationError(
            "Failed to generate questions after retries.",
            hint="Try a more capable model or reduce question count in config.yaml.",
        ) from last_error

    def _parse_questions(self, raw_list: list[dict]) -> list[Question]:
        """Convert raw dicts to validated Question models."""
        questions = []
        for i, raw in enumerate(raw_list):
            # Always override LLM-supplied IDs to guarantee uniqueness and sequential order.
            # If we trusted raw.get("id"), LLM-supplied collisions would silently corrupt
            # result storage which keys by question ID.
            raw["id"] = i + 1
            q_type = raw.get("type", "mcq")
            options = None
            if q_type == "mcq" and "options" in raw:
                options = [MCQOption(**o) for o in raw["options"]]
            questions.append(
                Question(
                    id=raw["id"],
                    type=q_type,
                    topic=raw.get("topic", "General"),
                    difficulty=raw.get("difficulty", "medium"),
                    bloom_level=raw.get("bloom_level"),
                    question=raw.get("question", ""),
                    options=options,
                    correct_answer=raw.get("correct_answer"),
                    explanation=raw.get("explanation"),
                    evaluation_rubric=raw.get("evaluation_rubric"),
                )
            )
        return questions
