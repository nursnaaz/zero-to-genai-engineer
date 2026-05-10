# Distill — Architecture

## System Diagram

```
Student Browser (React 18 + CloudScape)
     |
     | REST API
     v
FastAPI Backend (Python 3.10+)
     |
     | provider abstraction
     v
LLM Provider (Ollama / OpenAI / Anthropic / Gemini)
STT Provider (Whisper local / OpenAI Whisper / AWS Transcribe)
     |
     v
Session Store (In-memory / SQLite / PostgreSQL)
```

---

## Key Design Principles

**1. Zero hardcoding** — Every model name, URL, prompt, and threshold is in `config.yaml`. Changing provider = edit one line.

**2. Provider-agnostic services** — `TranscriptAnalyzer`, `QuestionGenerator`, and `AnswerEvaluator` only know about `BaseLLMProvider`. The factory creates the real implementation at startup.

**3. Prompts are data** — All prompt text lives in `.j2` Jinja2 templates in `backend/prompts/`. Change a prompt — no code change, no restart needed.

**4. Graceful degradation** — Voice fails? Auto-fallback to text. LLM returns invalid JSON? Retry up to `config.llm.retry_attempts` times with a clearer instruction.

**5. Config-driven features** — Every feature can be toggled in `config.yaml` (e.g., `ui.features.voice_waveform_enabled: false`).

---

## Request Flow (POST /api/analyze)

```
Client sends transcript text
  |
  v
AnalyzeRequest validated by Pydantic
  |
  v
TranscriptAnalyzer.analyze(transcript)
  |-- PromptManager.render("summary", transcript=...)
  |-- LLM.complete(messages) --> JSON --> SummaryResponse
  |-- PromptManager.render("concept_map", topics=..., concepts=...)
  |-- LLM.complete(messages) --> Mermaid syntax --> ConceptMapResponse
  |
  v
QuestionGenerator.generate(summary_dict, transcript)
  |-- PromptManager.render("questions", ...)
  |-- LLM.complete(messages) --> JSON --> [Question]
  |
  v
SessionStore.save_session(session_id, ...)
  |
  v
Return AnalyzeResponse {session_id, summary, questions, concept_map}
```

---

## Adding a New LLM Provider

1. Create `backend/providers/llm/my_provider.py`
2. Implement `BaseLLMProvider`: `complete()`, `get_provider_name()`, `get_model_name()`
3. Add one `elif` in `backend/providers/llm/factory.py`
4. Add config section in `config.yaml` under `llm:`
5. Done — no other files change

---

## Session State Machine

```
InputPage
  |
  | POST /api/analyze
  v
SummaryPage
  |
  | navigate
  v
AssessmentPage
  |
  | for each question:
  |   MCQ:  POST /api/evaluate/mcq --> update difficulty
  |   TIB:  POST /api/transcribe (voice) --> POST /api/evaluate/voice
  |
  | last question answered
  v
ResultsPage
```

---

## Phase Roadmap

| Phase | Storage | LLM | STT | Auth |
|---|---|---|---|---|
| 0 (now) | In-memory | Ollama local | Whisper local | None |
| 1 | SQLite | Any provider | Any provider | None |
| 2 | PostgreSQL | AWS Bedrock | AWS Transcribe | Supabase Auth |
| 3 | PostgreSQL multi-tenant | Any | Any | Multi-tenant + Stripe |
