from __future__ import annotations
"""AnswerEvaluator service.

Evaluates both MCQ answers (deterministic + LLM hint) and teach-it-back voice/text answers
(full LLM interview evaluation with 5 scoring dimensions).
"""

import json
from core.config import AppConfig
from core.exceptions import EvaluationError
from core.logging import get_logger
from core.prompt_manager import PromptManager
from core.utils import extract_json as _extract_json
from providers.llm.base import BaseLLMProvider, LLMMessage
from models.responses import (
    MCQEvaluationResponse,
    VoiceEvaluationResponse,
    DimensionScore,
)

logger = get_logger(__name__)


class AnswerEvaluator:
    """Evaluates student answers for both MCQ and teach-it-back question types."""

    def __init__(self, llm: BaseLLMProvider, prompt_mgr: PromptManager, config: AppConfig):
        self._llm = llm
        self._prompt = prompt_mgr
        self._config = config

    async def evaluate_mcq(
        self,
        question: dict,
        selected_answer: str,
        hint_level: int = 0,
    ) -> MCQEvaluationResponse:
        """Evaluate an MCQ answer. Determination is rule-based; LLM adds explanation/hint."""
        is_correct = selected_answer == question.get("correct_answer")
        correct_answer = question.get("correct_answer", "")
        options = {o["key"]: o["text"] for o in (question.get("options") or [])}

        prompt_text = self._prompt.render(
            "evaluate_mcq",
            question=question.get("question", ""),
            option_a=options.get("A", ""),
            option_b=options.get("B", ""),
            option_c=options.get("C", ""),
            option_d=options.get("D", ""),
            correct_answer=correct_answer,
            selected_answer=selected_answer,
            difficulty=question.get("difficulty", "medium"),
            hint_level=hint_level,
        )

        messages = [LLMMessage(role="user", content=prompt_text)]
        resp = None

        for attempt in range(1, self._config.llm.retry_attempts + 1):
            try:
                resp = await self._llm.complete(messages)
                raw = _extract_json(resp.content)
                data = json.loads(raw)

                # Determine adaptive difficulty
                difficulty = question.get("difficulty", "medium")
                if is_correct:
                    next_diff = {"easy": "medium", "medium": "hard", "hard": "hard"}.get(difficulty, "medium")
                else:
                    next_diff = {"hard": "medium", "medium": "easy", "easy": "easy"}.get(difficulty, "easy")

                # Trust server next_difficulty if LLM provided it and it's valid
                llm_next = data.get("next_difficulty", "")
                if llm_next in ("easy", "medium", "hard"):
                    next_diff = llm_next

                return MCQEvaluationResponse(
                    is_correct=is_correct,                # rule-based, not LLM
                    correct_answer=correct_answer,
                    explanation=data.get("explanation", ""),
                    hint=data.get("hint") if not is_correct else None,
                    next_difficulty=next_diff,
                )
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                logger.warning("MCQ eval parse failed", attempt=attempt, error=str(e))
                if attempt < self._config.llm.retry_attempts:
                    messages = messages + [
                        LLMMessage(role="assistant", content=resp.content if resp is not None else ""),
                        LLMMessage(role="user", content="Return ONLY valid JSON."),
                    ]

        # Fallback after all retries exhausted — log so operators know LLM enrichment failed.
        logger.error(
            "MCQ eval: all LLM attempts failed; returning correctness-only response",
            question_id=question.get("id"),
            retries=self._config.llm.retry_attempts,
        )
        difficulty = question.get("difficulty", "medium")
        next_diff = (
            {"easy": "medium", "medium": "hard", "hard": "hard"}.get(difficulty, "medium")
            if is_correct
            else "easy"
        )
        return MCQEvaluationResponse(
            is_correct=is_correct,
            correct_answer=correct_answer,
            explanation="",
            next_difficulty=next_diff,
        )

    async def evaluate_voice(
        self,
        question: dict,
        student_answer: str,
        session_context: str,
        was_voice: bool = True,
    ) -> VoiceEvaluationResponse:
        """Full LLM interview evaluation: 5 dimensions + narrative debrief + verdict."""
        prompt_text = self._prompt.render(
            "evaluate_voice",
            question=question.get("question", ""),
            evaluation_rubric=question.get("evaluation_rubric", ""),
            student_answer=student_answer,
            session_context=session_context,
            was_voice=was_voice,
            score_dimensions=[
                {"key": d.key, "label": d.label, "weight": d.weight}
                for d in self._config.evaluation.score_dimensions
            ],
        )

        messages = [LLMMessage(role="user", content=prompt_text)]
        resp = None

        for attempt in range(1, self._config.llm.retry_attempts + 1):
            try:
                resp = await self._llm.complete(messages)
                raw = _extract_json(resp.content)
                data = json.loads(raw)
                return self._parse_voice_evaluation(data)
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                logger.warning("Voice eval parse failed", attempt=attempt, error=str(e))
                if attempt < self._config.llm.retry_attempts:
                    messages = messages + [
                        LLMMessage(role="assistant", content=resp.content if resp is not None else ""),
                        LLMMessage(role="user", content="Return ONLY valid JSON matching the specified schema."),
                    ]

        raise EvaluationError(
            "Failed to evaluate voice answer after retries.",
            hint="The LLM returned unexpected output. Try again or check the model.",
        )

    def _parse_voice_evaluation(self, data: dict) -> VoiceEvaluationResponse:
        """Parse and validate LLM voice evaluation JSON."""
        raw_dims = data.get("dimension_scores", [])
        dimension_scores = []
        total_weighted = 0.0
        total_weight = 0.0

        for dim in raw_dims:
            score = max(1, min(5, int(dim.get("score", 3))))  # clamp to [1, 5]
            weight = float(dim.get("weight", 0.2))
            dimension_scores.append(
                DimensionScore(
                    key=dim.get("key", ""),
                    label=dim.get("label", ""),
                    score=score,
                    weight=weight,
                )
            )
            total_weighted += score * weight
            total_weight += weight

        # Normalise in case weights don't sum to 1.0
        weighted_score = total_weighted / total_weight if total_weight > 0 else 3.0
        weighted_score = round(max(1.0, min(5.0, weighted_score)), 2)

        # Map verdict string to cloudscape type using config thresholds
        verdict_label = data.get("verdict", "Developing — needs more practice")
        verdict_type = "warning"  # default
        for v in sorted(
            self._config.evaluation.verdicts,
            key=lambda x: x.min_weighted_score,
            reverse=True,
        ):
            if weighted_score >= v.min_weighted_score:
                verdict_label = v.label
                verdict_type = v.cloudscape_type
                break

        recs = data.get("study_recommendations", [])
        max_recs = self._config.evaluation.output.max_recommendations
        return VoiceEvaluationResponse(
            dimension_scores=dimension_scores,
            weighted_score=weighted_score,
            narrative_debrief=data.get("narrative_debrief", ""),
            verdict=verdict_label,
            verdict_type=verdict_type,
            follow_up_question=data.get("follow_up_question"),
            study_recommendations=recs[:max_recs],
        )
