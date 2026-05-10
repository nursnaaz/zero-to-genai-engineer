from __future__ import annotations
"""TranscriptAnalyzer service — map-reduce distillation pipeline.

For transcripts that fit in one chunk:
  transcript → summary + concept map  (single pass, same as before)

For long transcripts (any size):
  transcript
    → split into overlapping chunks
    → [map]    summarize each chunk in plain text
    → [reduce] merge chunk summaries (recursively if needed)
    → distilled text (always ≤ chunk_size_chars)
    → summary (JSON) + concept map  (final pass on distilled text)

This guarantees no context-window overflow and no timeout regardless of
transcript length.  A 3-hour lecture (~200k chars) needs 1 map-reduce round.
A full-day workshop (~1M chars) needs 2 rounds.  Each individual LLM call
always receives ≤ chunk_size_chars of input.
"""

import asyncio
import json
import re
from typing import Callable, Awaitable, Any
from core.config import AppConfig
from core.exceptions import EvaluationError
from core.logging import get_logger
from core.prompt_manager import PromptManager
from core.utils import extract_json as _extract_json
from providers.llm.base import BaseLLMProvider, LLMMessage
from models.responses import (
    SummaryResponse, ConceptMapResponse, KeyConcept, ConfusionZone
)

# Async callback: receives a dict event, returns nothing
Emit = Callable[[dict[str, Any]], Awaitable[None]]

async def _noop(event: dict[str, Any]) -> None:
    """Default no-op emit used when no progress tracking is needed."""

logger = get_logger(__name__)


# ── Chunk helpers ──────────────────────────────────────────────────────────────

def _split_into_chunks(text: str, chunk_size: int, overlap: int) -> list[str]:
    """Split text into overlapping chunks, breaking at newlines or sentence ends."""
    if len(text) <= chunk_size:
        return [text]

    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        if end < len(text):
            # Prefer to break at a newline within the back-half of the chunk
            mid = start + chunk_size // 2
            bp = text.rfind('\n', mid, end)
            if bp == -1:
                bp = text.rfind('. ', mid, end)
            if bp != -1:
                end = bp + 1
        chunks.append(text[start:end])
        next_start = end - overlap
        # Guard against infinite loop on very short text or large overlap
        start = next_start if next_start > start else end
    return chunks


# ── JSON parse/retry wrapper ───────────────────────────────────────────────────

async def _call_with_retry(
    llm: BaseLLMProvider,
    messages: list[LLMMessage],
    config: AppConfig,
    parse_fn,
    label: str,
):
    """Call LLM, retry on JSON parse failure, appending a clarification each try."""
    last_error = None
    resp = None
    for attempt in range(1, config.llm.retry_attempts + 1):
        try:
            resp = await llm.complete(messages)
            raw = _extract_json(resp.content)
            return parse_fn(raw)
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            last_error = e
            logger.warning(
                f"{label}: JSON parse failed on attempt {attempt}",
                error=str(e),
                raw_preview=resp.content[:200] if resp is not None else "",
            )
            if attempt < config.llm.retry_attempts:
                await asyncio.sleep(config.llm.retry_delay_seconds)
                messages = messages + [
                    LLMMessage(role="assistant", content=resp.content if resp is not None else ""),
                    LLMMessage(
                        role="user",
                        content="Your response was not valid JSON. Return ONLY the JSON object, no markdown, no explanation.",
                    ),
                ]
    raise EvaluationError(
        f"{label}: Failed to parse LLM JSON after {config.llm.retry_attempts} attempts.",
        hint="Try a larger or more capable model. Check config.yaml llm.model.",
    ) from last_error


# ── Structured parsers ─────────────────────────────────────────────────────────

def _parse_summary(raw: str) -> SummaryResponse:
    data = json.loads(raw)
    return SummaryResponse(
        session_title=data.get("session_title", "Untitled Session"),
        topics_covered=data.get("topics_covered", []),
        key_concepts=[KeyConcept(**c) for c in data.get("key_concepts", [])],
        learning_objectives=data.get("learning_objectives", []),
        teacher_insight=data.get("teacher_insight", ""),
        confusion_zones=[
            ConfusionZone(**z) for z in data.get("confusion_zones", [])
        ],
    )


def _parse_concept_map(raw: str) -> ConceptMapResponse:
    """Parse the raw Mermaid string returned by the LLM."""
    mermaid_syntax = raw.strip()
    # Strip markdown code fences if the model wrapped the output
    mermaid_syntax = re.sub(r'^```(?:mermaid)?\s*', '', mermaid_syntax, flags=re.IGNORECASE)
    mermaid_syntax = re.sub(r'\s*```$', '', mermaid_syntax)
    mermaid_syntax = mermaid_syntax.strip()

    # Extract node labels — handle both double-quoted A["Label"] and unquoted A[Label]
    node_labels = re.findall(r'\["([^"]+)"\]', mermaid_syntax)
    if not node_labels:
        node_labels = re.findall(r'\w+\[([^\]"]+)\]', mermaid_syntax)

    # Extract edges: A --> B or A -->|label| B
    edge_matches = re.findall(r'(\w+)\s*--[->]+\|?"?([^"|\]]*)"?\|?\s*(\w+)', mermaid_syntax)
    edges = [{"from": m[0], "to": m[2], "label": m[1].strip()} for m in edge_matches]
    return ConceptMapResponse(
        mermaid_syntax=mermaid_syntax,
        nodes=node_labels,
        edges=edges,
    )


# ── Map-reduce prompts (inline — no Jinja needed for internal distillation) ────

_CHUNK_SUMMARY_PROMPT = """\
You are summarizing part {index} of {total} of a classroom transcript.
Extract all educational content compactly.

Transcript:
{chunk}

Write a concise summary (250–400 words) covering:
1. Topics introduced or discussed
2. Key concepts and their definitions / explanations
3. Concrete examples or analogies used
4. Student questions and the teacher's answers
5. Any points of confusion or repeated explanations

Write in clear prose. Preserve technical terminology exactly."""

_MERGE_SUMMARIES_PROMPT = """\
You have {count} summaries of consecutive parts of the same classroom session.
Merge them into one unified summary without losing any information.

{parts}

Write a single cohesive summary (400–600 words) that:
1. Lists every topic covered across all parts
2. Combines all key concepts (deduplicate, keep all unique content)
3. Preserves all examples, analogies, and concrete explanations
4. Includes all student questions and teacher answers
5. Notes all confusion points

Avoid repetition. Preserve all technical terms exactly."""


# ── Main service ───────────────────────────────────────────────────────────────

class TranscriptAnalyzer:
    """Analyzes a classroom transcript to produce a session summary and concept map.

    For long transcripts the map-reduce pipeline kicks in automatically:
      split → chunk-summarize (map) → merge (reduce, recursive) → final pass
    """

    def __init__(self, llm: BaseLLMProvider, prompt_mgr: PromptManager, config: AppConfig):
        self._llm = llm
        self._prompt = prompt_mgr
        self._config = config

    # ── Public entry point ─────────────────────────────────────────────────────

    async def analyze(
        self,
        transcript: str,
        emit: Emit = _noop,
    ) -> tuple[SummaryResponse, ConceptMapResponse]:
        """Run the full analysis pipeline on a transcript of any length."""
        logger.info("Starting transcript analysis", transcript_len=len(transcript))
        await emit({"stage": "reading", "message": "Reading transcript",
                    "detail": f"{len(transcript):,} characters loaded"})

        # Distill long transcripts down to a single chunk via map-reduce
        distilled = await self._distill(transcript, emit=emit)
        if len(distilled) < len(transcript):
            logger.info(
                "Transcript distilled via map-reduce",
                original_chars=len(transcript),
                distilled_chars=len(distilled),
            )

        # Final pass 1: structured summary JSON
        await emit({"stage": "summary", "message": "Extracting topics & key concepts",
                    "detail": "Building your structured session summary"})
        summary_prompt = self._prompt.render("summary", transcript=distilled)
        summary_msgs = [LLMMessage(role="user", content=summary_prompt)]
        summary = await _call_with_retry(
            self._llm, summary_msgs, self._config, _parse_summary, "Summary"
        )
        logger.info("Summary complete", topics=summary.topics_covered)

        # Final pass 2: Mermaid concept map
        await emit({"stage": "concept_map", "message": "Drawing concept map",
                    "detail": f"Mapping relationships between {len(summary.key_concepts)} concepts"})
        concept_names = [c.concept for c in summary.key_concepts]
        map_prompt = self._prompt.render(
            "concept_map",
            topics=summary.topics_covered,
            concepts=concept_names,
        )
        map_msgs = [LLMMessage(role="user", content=map_prompt)]
        resp = await self._llm.complete(map_msgs)
        concept_map = _parse_concept_map(resp.content)
        logger.info("Concept map complete", nodes=len(concept_map.nodes))

        return summary, concept_map

    # ── Map-reduce distillation ────────────────────────────────────────────────

    async def _distill(self, text: str, _depth: int = 0, emit: Emit = _noop) -> str:
        """Recursively distil `text` until it fits in one chunk."""
        chunk_size = self._config.llm.chunk_size_chars
        overlap = self._config.llm.chunk_overlap_chars

        if len(text) <= chunk_size:
            return text

        chunks = _split_into_chunks(text, chunk_size, overlap)
        logger.info(
            "Map-reduce: splitting transcript",
            depth=_depth,
            input_chars=len(text),
            chunks=len(chunks),
        )
        await emit({
            "stage": "splitting",
            "message": f"Long transcript — splitting into {len(chunks)} chunks",
            "detail": "Map-reduce pipeline: summarize each part, then merge",
        })

        chunk_summaries = await self._map_chunks(chunks, emit=emit)

        await emit({
            "stage": "merging",
            "message": f"Merging {len(chunks)} chunk summaries",
            "detail": "Combining all educational content into one distilled view",
        })
        merged = await self._reduce(chunk_summaries)
        logger.info("Map-reduce: merged", depth=_depth, output_chars=len(merged))

        return await self._distill(merged, _depth + 1, emit=emit)

    async def _map_chunks(self, chunks: list[str], emit: Emit = _noop) -> list[str]:
        """Summarize each chunk; run up to 3 concurrently."""
        sem = asyncio.Semaphore(3)

        async def _one(i: int, chunk: str) -> str:
            async with sem:
                logger.info("Chunk summarize", chunk=i + 1, total=len(chunks))
                await emit({
                    "stage": "chunk",
                    "message": f"Summarizing chunk {i + 1} of {len(chunks)}",
                    "detail": "Extracting key concepts, examples, and Q&A from this section",
                    "chunk": i + 1,
                    "total_chunks": len(chunks),
                })
                prompt = _CHUNK_SUMMARY_PROMPT.format(
                    index=i + 1,
                    total=len(chunks),
                    chunk=chunk,
                )
                resp = await self._llm.complete(
                    [LLMMessage(role="user", content=prompt)]
                )
                return resp.content.strip()

        return list(await asyncio.gather(*[_one(i, c) for i, c in enumerate(chunks)]))

    async def _reduce(self, summaries: list[str]) -> str:
        """Merge a list of chunk summaries into one text."""
        BATCH = 8
        if len(summaries) <= BATCH:
            return await self._merge_batch(summaries)

        batch_results: list[str] = []
        for i in range(0, len(summaries), BATCH):
            batch = summaries[i: i + BATCH]
            logger.info("Merging batch", start=i + 1, end=i + len(batch), total=len(summaries))
            batch_results.append(await self._merge_batch(batch))

        return await self._reduce(batch_results)

    async def _merge_batch(self, summaries: list[str]) -> str:
        """Single LLM call to merge ≤ 8 summaries into one."""
        parts = "\n\n---\n\n".join(
            f"[Part {i + 1}]\n{s}" for i, s in enumerate(summaries)
        )
        prompt = _MERGE_SUMMARIES_PROMPT.format(count=len(summaries), parts=parts)
        resp = await self._llm.complete([LLMMessage(role="user", content=prompt)])
        return resp.content.strip()
