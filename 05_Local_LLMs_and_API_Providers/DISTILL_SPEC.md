# Distill — Complete Technical Specification
# Claude Code Prompt: Build this project end-to-end from this specification.

---

## 0. Instructions for Claude Code

Build the Distill project exactly as specified in this document. Follow this order:
1. Scaffold the full directory structure first
2. Write config.yaml and core/config.py
3. Implement provider abstractions (LLM + STT) before any routes
4. Write all prompt templates as Jinja2 files
5. Wire services → routers → main.py
6. Build the React frontend last, once the API is complete
7. Write README.md with exact setup commands

Do not hardcode any model names, API keys, URLs, or prompt text in Python or TypeScript files.
All such values must come from config.yaml or environment variables.

---

## 1. Project Overview

**Name:** Distill  
**Tagline:** Pure knowledge, every class  
**Brand:** Inceptez  
**Version:** 0.1.0 (Phase 0 — local classroom demo)

Distill takes a Teams/Zoom meeting transcript, generates a structured session summary with
a concept map, and then runs a hybrid assessment: adaptive MCQ questions + "Teach It Back"
voice-evaluated interview-style questions. The result is a detailed, narrative interview
debrief showing exactly where the student is strong and where they need to improve.

**Key design principle:** Zero hardcoding. Every model name, URL, prompt, threshold, persona,
and feature flag lives in config.yaml. Swapping from Ollama to Anthropic is a one-line
config change. Adding a new LLM provider is adding one file.

---

## 2. Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    Student Browser                       │
│  React 18 + Vite + AWS CloudScape Design System         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│  │  Input   │ │ Summary  │ │  Quiz    │ │ Results  │  │
│  │  Page    │→│+ Concept │→│MCQ+Voice │→│Interview │  │
│  │ (Wizard) │ │   Map    │ │ Adaptive │ │ Debrief  │  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘  │
│  MediaRecorder API → audio blob → POST /api/transcribe  │
└────────────────────────┬────────────────────────────────┘
                         │ REST API (JSON + multipart)
                         ▼
┌─────────────────────────────────────────────────────────┐
│              FastAPI Backend (Python 3.11+)              │
│                                                          │
│  Routers: /api/analyze  /api/transcribe  /api/evaluate  │
│            /api/session  /api/health  /api/config/ui    │
│                                                          │
│  Services:  Analyzer │ Assessor │ Evaluator             │
│                                                          │
│  Core:  ConfigLoader │ PromptManager │ SessionStore      │
│                                                          │
│  ┌──────────────────────────┐  ┌─────────────────────┐  │
│  │   LLM Provider Layer     │  │   STT Provider Layer │  │
│  │  (reads provider from    │  │  (reads provider from│  │
│  │   config.yaml)           │  │   config.yaml)       │  │
│  │                          │  │                      │  │
│  │  BaseLLMProvider         │  │  BaseSTTProvider     │  │
│  │  ├─OpenAICompatible      │  │  ├─WhisperLocal      │  │
│  │  │  ├─Ollama             │  │  ├─OpenAIWhisper     │  │
│  │  │  ├─LMStudio           │  │  ├─AWSTranscribe     │  │
│  │  │  └─OpenAI             │  │  └─GoogleSTT         │  │
│  │  ├─AnthropicProvider     │  │                      │  │
│  │  ├─GeminiProvider        │  └─────────────────────┘  │
│  │  └─LangChainProvider     │                            │
│  └──────────────────────────┘                            │
└────────────────────────┬────────────────────────────────┘
                         │
          ┌──────────────┴──────────────┐
          ▼                             ▼
  ┌───────────────┐            ┌───────────────┐
  │  Local LLMs   │            │  Cloud LLMs   │
  │  Ollama:11434 │            │  OpenAI API   │
  │  LMStudio:1234│            │  Anthropic API│
  │  Gemma3/Llama │            │  Gemini API   │
  └───────────────┘            └───────────────┘
```

---

## 3. Technology Stack

### Backend
- Python 3.11+
- FastAPI 0.115+
- Uvicorn (ASGI server)
- Pydantic v2 (data validation + settings)
- PyYAML (config loading)
- Jinja2 (prompt templates)
- openai-whisper (local STT — whisper_local provider)
- openai (SDK — used for Ollama, LM Studio, OpenAI providers)
- anthropic (SDK — Anthropic provider)
- google-generativeai (SDK — Gemini provider)
- langchain + langchain-community (LangChain provider)
- httpx (async HTTP)
- python-dotenv (env vars)
- python-multipart (audio file uploads)
- aiofiles (async file I/O)
- structlog (structured logging)

### Frontend
- Node.js 20+
- React 18
- TypeScript 5
- Vite 5
- @cloudscape-design/components (AWS CloudScape)
- @cloudscape-design/global-styles
- @cloudscape-design/design-tokens
- React Router v6
- Axios
- mermaid (concept map rendering)
- @types/react, @types/node

### Dev Tools
- ruff (Python linting)
- black (Python formatting)
- pytest + httpx (backend tests)
- eslint + prettier (frontend)
- make (task runner via Makefile)

---

## 4. Directory Structure

```
distill/
├── config.yaml                    # PRIMARY config — edit this, not code
├── config.example.yaml            # Full reference with all options + comments
├── .env.example                   # API keys template
├── .env                           # Local secrets (gitignored)
├── .gitignore
├── README.md                      # Setup + usage guide
├── Makefile                       # dev, build, test, lint commands
│
├── backend/
│   ├── main.py                    # FastAPI app entry + middleware
│   ├── requirements.txt
│   ├── requirements-dev.txt       # test + lint deps
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py              # YAML loader → AppConfig dataclass
│   │   ├── logging.py             # structlog setup
│   │   ├── exceptions.py          # custom exceptions + HTTP error handlers
│   │   └── prompt_manager.py     # Jinja2 template loader + renderer
│   │
│   ├── providers/
│   │   ├── __init__.py
│   │   ├── llm/
│   │   │   ├── __init__.py
│   │   │   ├── base.py            # BaseLLMProvider ABC
│   │   │   ├── factory.py         # create_llm_provider(config) → BaseLLMProvider
│   │   │   ├── openai_compatible.py  # Handles Ollama + LM Studio + OpenAI
│   │   │   ├── anthropic_provider.py
│   │   │   ├── gemini_provider.py
│   │   │   └── langchain_provider.py
│   │   └── stt/
│   │       ├── __init__.py
│   │       ├── base.py            # BaseSTTProvider ABC
│   │       ├── factory.py         # create_stt_provider(config) → BaseSTTProvider
│   │       ├── whisper_local.py
│   │       ├── openai_whisper.py
│   │       ├── aws_transcribe.py
│   │       └── google_stt.py
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── analyzer.py            # TranscriptAnalyzer: summary + concept map + confusion
│   │   ├── assessor.py            # QuestionGenerator: MCQ + teach-it-back questions
│   │   └── evaluator.py          # AnswerEvaluator: MCQ eval + voice interview eval
│   │
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── analyze.py             # POST /api/analyze
│   │   ├── transcribe.py          # POST /api/transcribe
│   │   ├── evaluate.py            # POST /api/evaluate/mcq + /api/evaluate/voice
│   │   ├── sessions.py            # GET /api/sessions + GET /api/session/{id}
│   │   └── system.py              # GET /api/health + GET /api/config/ui
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── requests.py            # Pydantic request models
│   │   └── responses.py           # Pydantic response models
│   │
│   ├── storage/
│   │   ├── __init__.py
│   │   ├── base.py                # BaseSessionStore ABC
│   │   ├── memory_store.py        # In-memory (Phase 0)
│   │   └── sqlite_store.py        # SQLite (Phase 1)
│   │
│   ├── prompts/
│   │   ├── summary_system.j2
│   │   ├── questions_system.j2
│   │   ├── concept_map_system.j2
│   │   ├── evaluate_mcq_system.j2
│   │   ├── evaluate_voice_system.j2
│   │   └── confusion_map_system.j2
│   │
│   └── tests/
│       ├── __init__.py
│       ├── test_providers.py      # T18 — provider integration tests
│       ├── test_services.py       # service unit tests
│       └── test_routers.py        # API endpoint tests (httpx TestClient)
│
├── data/                          # created at runtime; gitignored
│   └── .gitkeep
│
└── frontend/
    ├── package.json
    ├── vite.config.ts
    ├── tsconfig.json
    ├── index.html
    └── src/
        ├── main.tsx
        ├── App.tsx
        ├── router.tsx
        │
        ├── config/
        │   └── api.ts              # axios instance + base URL
        │
        ├── api/
        │   ├── analyze.ts
        │   ├── transcribe.ts
        │   ├── evaluate.ts
        │   └── sessions.ts
        │
        ├── types/
        │   ├── session.ts
        │   ├── assessment.ts
        │   └── evaluation.ts
        │
        ├── context/
        │   └── AppContext.tsx       # React Context + useReducer global state
        │
        ├── hooks/
        │   ├── useSession.ts        # consume AppContext; expose session actions
        │   ├── useVoiceRecorder.ts
        │   └── useAdaptiveDifficulty.ts
        │
        ├── components/
        │   ├── layout/
        │   │   ├── AppShell.tsx    # CloudScape AppLayout + TopNavigation
        │   │   └── SessionSidebar.tsx  # SideNavigation with session history
        │   ├── transcript/
        │   │   └── TranscriptInput.tsx  # Textarea + FileUpload + student name
        │   ├── summary/
        │   │   ├── SessionSummary.tsx   # Topics, concepts, objectives
        │   │   ├── ConceptMap.tsx       # Mermaid.js renderer
        │   │   └── ConfusionZones.tsx   # Friction moments from transcript
        │   ├── assessment/
        │   │   ├── MCQQuestion.tsx      # RadioGroup + hint system + feedback
        │   │   ├── TeachItBack.tsx      # Voice/text toggle + recorder + transcript
        │   │   ├── VoiceRecorder.tsx    # MediaRecorder + waveform + timer
        │   │   └── DifficultyBadge.tsx  # Easy/Medium/Hard badge
        │   └── results/
        │       ├── InterviewDebrief.tsx  # ExpandableSection per question
        │       ├── TopicBreakdown.tsx    # Table + ProgressBar per topic
        │       ├── ScoreDimensions.tsx   # Five-dimension spider chart (text-based)
        │       └── WhatsAppExport.tsx    # CopyToClipboard formatted summary
        │
        └── pages/
            ├── InputPage.tsx
            ├── SummaryPage.tsx
            ├── AssessmentPage.tsx
            └── ResultsPage.tsx
```

---

## 5. Configuration File (config.yaml)

Create this file at the project root. This is the ONLY place to change settings.

```yaml
# config.yaml
# Distill — Master Configuration
# Override any value with env var: DISTILL_<SECTION>_<KEY>
# Example: DISTILL_LLM_PROVIDER=anthropic

app:
  name: "Distill"
  version: "0.1.0"
  brand_name: "Distill"
  brand_tagline: "Pure knowledge, every class"
  debug: false
  log_level: "INFO"   # DEBUG | INFO | WARNING | ERROR

server:
  host: "0.0.0.0"
  port: 8000
  cors_origins:
    - "http://localhost:5173"
    - "http://localhost:3000"
  max_upload_size_mb: 50

# ─── LLM PROVIDER ────────────────────────────────────────────────────────────
# Set provider to one of: ollama | lmstudio | openai | anthropic | gemini | langchain
# The active provider reads its settings from the matching subsection below.

llm:
  provider: "ollama"
  model: "gemma3:9b"
  temperature: 0.3
  max_tokens: 4000
  timeout_seconds: 120
  retry_attempts: 3
  retry_delay_seconds: 2

  ollama:
    base_url: "http://localhost:11434"
    # model overrides llm.model if set here
    keep_alive: "5m"

  lmstudio:
    base_url: "http://localhost:1234/v1"
    api_key: "lm-studio"    # LM Studio requires any non-empty string

  openai:
    base_url: "https://api.openai.com/v1"
    # api_key: set via DISTILL_LLM_API_KEY or OPENAI_API_KEY env var
    organization: null

  anthropic:
    base_url: "https://api.anthropic.com"
    # api_key: set via DISTILL_LLM_API_KEY or ANTHROPIC_API_KEY env var
    api_version: "2023-06-01"

  gemini:
    base_url: "https://generativelanguage.googleapis.com/v1beta"
    # api_key: set via DISTILL_LLM_API_KEY or GOOGLE_API_KEY env var

  langchain:
    backend: "ollama"       # which backend LangChain wraps
    tracing_enabled: false
    tracing_project: "distill"

# ─── SPEECH TO TEXT ──────────────────────────────────────────────────────────
# Set provider to one of: whisper_local | openai_whisper | aws_transcribe | google_stt

speech_to_text:
  provider: "whisper_local"
  language: "en"

  whisper_local:
    model_size: "medium"    # tiny | base | small | medium | large-v3
    device: "cpu"           # cpu | cuda | mps
    compute_type: "float32" # float32 | float16 | int8 (int8 for faster CPU)
    download_on_startup: true

  openai_whisper:
    model: "whisper-1"
    # api_key: from OPENAI_API_KEY env var

  aws_transcribe:
    region: "us-east-1"
    s3_bucket: null

  google_stt:
    credentials_path: null

# ─── ASSESSMENT CONFIGURATION ─────────────────────────────────────────────────

assessment:
  mcq:
    count: 5
    difficulty_distribution:
      easy: 0.30
      medium: 0.50
      hard: 0.20
    show_hints: true
    hint_levels: 3
    show_explanation_after_answer: true
    time_limit_seconds: null

  teach_it_back:
    count: 3
    min_answer_words: 20
    max_recording_seconds: 120
    allow_retake: true
    voice_enabled: true
    text_fallback: true

  bloom_taxonomy:
    enabled: true
    distribution:
      remember: 0.20
      understand: 0.30
      apply: 0.30
      analyze: 0.10
      evaluate: 0.10

  adaptive_engine:
    enabled: true
    initial_difficulty: "medium"
    increase_after_consecutive_correct: 2
    decrease_after_consecutive_wrong: 1
    per_topic_tracking: true

# ─── EVALUATION & INTERVIEWER PERSONA ─────────────────────────────────────────

evaluation:
  interviewer:
    name: "Dr. Priya"
    persona: >
      You are a Senior Applied Scientist who has conducted 400+ technical interviews
      over 12 years at top AI companies. You are known for being precise, fair, and
      deeply honest. You never give empty praise. When you say 'strong answer,' it
      means something. When you identify a gap, you name it exactly — not vague
      advice, but the specific concept, term, or mechanism they missed.
    style: "Structured, warm but honest, always constructive, never generic"
    domain: "Artificial Intelligence, Machine Learning, and Generative AI"

  score_dimensions:
    - key: "accuracy"
      label: "Technical Accuracy"
      weight: 0.30
      description: "Are the core facts and concepts correct?"
    - key: "depth"
      label: "Conceptual Depth"
      weight: 0.25
      description: "Does the answer go beyond surface-level understanding?"
    - key: "clarity"
      label: "Clarity of Explanation"
      weight: 0.20
      description: "Could a peer understand this explanation?"
    - key: "examples"
      label: "Use of Examples"
      weight: 0.15
      description: "Are concrete examples used to support the answer?"
    - key: "connections"
      label: "Concept Connections"
      weight: 0.10
      description: "Does the answer connect to other topics from the session?"

  verdicts:
    - label: "Strong — interview ready"
      min_weighted_score: 4.2
      cloudscape_type: "success"
    - label: "Good — minor gaps to address"
      min_weighted_score: 3.0
      cloudscape_type: "info"
    - label: "Developing — needs more practice"
      min_weighted_score: 2.0
      cloudscape_type: "warning"
    - label: "Foundational — revisit core concepts"
      min_weighted_score: 0.0
      cloudscape_type: "error"

  output:
    debrief_paragraph_count: 3
    quote_student_answer: true     # Include student's words in feedback
    include_follow_up_question: true
    include_study_recommendations: true
    max_recommendations: 3

# ─── CONCEPT MAP ──────────────────────────────────────────────────────────────

concept_map:
  renderer: "mermaid"        # mermaid (Phase 0) | d3 | cytoscape (Phase 2+)
  direction: "TD"            # TD | LR
  color_by_performance: true # update node colors after quiz completion
  show_dependencies: true    # show prerequisite relationships between concepts
  max_nodes: 20              # limit for readability

# ─── SESSION STORAGE ──────────────────────────────────────────────────────────

session:
  storage: "memory"          # memory (Phase 0) | sqlite (Phase 1) | postgresql (Phase 2+)
  sqlite_path: "./data/sessions.db"
  database_url: null         # postgresql://user:pass@host/db
  max_sessions_in_memory: 100

# ─── PROMPTS ──────────────────────────────────────────────────────────────────

prompts:
  directory: "./prompts"
  templates:
    summary: "summary_system.j2"
    questions: "questions_system.j2"
    concept_map: "concept_map_system.j2"
    evaluate_mcq: "evaluate_mcq_system.j2"
    evaluate_voice: "evaluate_voice_system.j2"
    confusion_map: "confusion_map_system.j2"

# ─── EXPORT FEATURES ──────────────────────────────────────────────────────────

export:
  whatsapp:
    enabled: true
    include_score: true
    include_verdict: true
    include_weak_areas: true
    include_study_tip: true
    footer_text: "Generated by Distill · Inceptez"
  anki:
    enabled: true            # export wrong MCQ answers as Anki-compatible CSV
  pdf:
    enabled: false           # Phase 2

# ─── UI CONFIGURATION ─────────────────────────────────────────────────────────

ui:
  cloudscape_theme: "default"
  sidebar:
    show_session_history: true
    max_history_items: 20
  wizard:
    allow_back_navigation: true
  features:
    confusion_map_enabled: true
    bloom_labels_visible: true
    timer_visible: false
    voice_waveform_enabled: true
```

---

## 6. Environment Variables (.env)

```bash
# .env — Never commit this file

# Frontend (Vite reads VITE_* prefixed vars only)
VITE_API_URL=http://localhost:8000   # backend base URL; override for production

# LLM API Keys (only needed for cloud providers)
DISTILL_LLM_API_KEY=           # generic — used when provider-specific key not set
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
GOOGLE_API_KEY=

# AWS (for aws_transcribe STT provider)
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_DEFAULT_REGION=us-east-1

# LangSmith (optional tracing)
LANGCHAIN_API_KEY=
LANGCHAIN_TRACING_V2=false
```

---

## 7. Data Models

### 7.1 Backend — Pydantic Models (backend/models/)

```python
# backend/models/requests.py

from pydantic import BaseModel, Field
from typing import Literal

class AnalyzeRequest(BaseModel):
    transcript: str = Field(..., min_length=100, description="Full meeting transcript text")
    student_name: str = Field(default="Student", max_length=100)
    session_label: str | None = Field(default=None, max_length=200)

class TranscribeRequest(BaseModel):
    # Audio sent as multipart FormData, not JSON body
    pass

class MCQEvaluateRequest(BaseModel):
    session_id: str
    question_id: int
    selected_answer: Literal["A", "B", "C", "D"]
    time_taken_seconds: int | None = None
    hint_level_used: int = Field(default=0, ge=0, le=3)

class VoiceEvaluateRequest(BaseModel):
    session_id: str
    question_id: int
    student_answer: str = Field(..., min_length=10)
    answer_duration_seconds: float | None = None
    was_voice: bool = True

# backend/models/responses.py

from pydantic import BaseModel
from typing import Literal
from datetime import datetime

class KeyConcept(BaseModel):
    concept: str
    explanation: str
    topic: str

class ConfusionZone(BaseModel):
    topic: str
    signal_type: Literal["student_question", "teacher_repeated", "explicit_check", "silence"]
    description: str
    timestamp_approx: str | None = None

class SummaryResponse(BaseModel):
    session_title: str
    topics_covered: list[str]
    key_concepts: list[KeyConcept]
    learning_objectives: list[str]
    teacher_insight: str
    confusion_zones: list[ConfusionZone]

class MCQOption(BaseModel):
    key: Literal["A", "B", "C", "D"]
    text: str

class Question(BaseModel):
    id: int
    type: Literal["mcq", "teach_it_back"]
    topic: str
    difficulty: Literal["easy", "medium", "hard"]
    bloom_level: Literal["remember", "understand", "apply", "analyze", "evaluate"] | None
    question: str
    options: list[MCQOption] | None = None   # MCQ only
    correct_answer: str | None = None        # MCQ only (A/B/C/D)
    explanation: str | None = None           # MCQ only
    evaluation_rubric: str | None = None     # teach_it_back only

class ConceptMapResponse(BaseModel):
    mermaid_syntax: str
    nodes: list[str]
    edges: list[dict]   # [{from, to, label}]

class AnalyzeResponse(BaseModel):
    session_id: str
    summary: SummaryResponse
    questions: list[Question]
    concept_map: ConceptMapResponse

class TranscribeResponse(BaseModel):
    transcript: str
    duration_seconds: float | None = None
    language_detected: str | None = None

class MCQEvaluationResponse(BaseModel):
    is_correct: bool
    correct_answer: str
    explanation: str
    hint: str | None = None
    next_difficulty: Literal["easy", "medium", "hard"]

class DimensionScore(BaseModel):
    key: str
    label: str
    score: int = Field(ge=1, le=5)
    weight: float

class VoiceEvaluationResponse(BaseModel):
    dimension_scores: list[DimensionScore]
    weighted_score: float = Field(ge=1.0, le=5.0)
    narrative_debrief: str          # 3 paragraphs separated by \n\n
    verdict: str
    verdict_type: Literal["success", "info", "warning", "error"]
    follow_up_question: str | None = None
    study_recommendations: list[str] = Field(default_factory=list, max_length=3)  # matches config.evaluation.output.max_recommendations

class SessionMeta(BaseModel):
    session_id: str
    student_name: str
    session_label: str | None
    created_at: datetime
    mcq_score_pct: float | None = None
    overall_verdict: str | None = None
    topics_covered: list[str] = []

class SessionResults(BaseModel):
    mcq_results: list[dict]          # {question_id, selected, is_correct, correct_answer, explanation}
    voice_results: list[dict]        # {question_id, student_answer, dimension_scores, weighted_score, verdict}
    topic_scores: dict[str, dict]    # topic → {correct, total, avg_voice_score}
    overall_mcq_pct: float
    overall_voice_score: float       # weighted average across teach-it-back questions

class HealthResponse(BaseModel):
    status: Literal["ok", "degraded", "error"]
    llm_provider: str
    llm_model: str
    stt_provider: str
    version: str

class UIConfigResponse(BaseModel):
    brand_name: str
    brand_tagline: str
    features: dict
    assessment_config: dict
```

### 7.2 Frontend — TypeScript Types (frontend/src/types/)

```typescript
// frontend/src/types/session.ts
export interface SessionMeta {
  session_id: string;
  student_name: string;
  session_label?: string;
  created_at: string;
  mcq_score_pct?: number;
  overall_verdict?: string;
  topics_covered: string[];
}

// frontend/src/types/assessment.ts
export type Difficulty = "easy" | "medium" | "hard";
export type BloomLevel = "remember" | "understand" | "apply" | "analyze" | "evaluate";
export type QuestionType = "mcq" | "teach_it_back";
export type AnswerKey = "A" | "B" | "C" | "D";

export interface MCQOption { key: AnswerKey; text: string; }

export interface Question {
  id: number;
  type: QuestionType;
  topic: string;
  difficulty: Difficulty;
  bloom_level?: BloomLevel;
  question: string;
  options?: MCQOption[];
  correct_answer?: AnswerKey;
  explanation?: string;
  evaluation_rubric?: string;
}

export interface KeyConcept { concept: string; explanation: string; topic: string; }
export interface ConfusionZone { topic: string; signal_type: string; description: string; }

export interface SummaryData {
  session_title: string;
  topics_covered: string[];
  key_concepts: KeyConcept[];
  learning_objectives: string[];
  teacher_insight: string;
  confusion_zones: ConfusionZone[];
}

export interface ConceptMap { mermaid_syntax: string; }

export interface AnalyzeResult {
  session_id: string;
  summary: SummaryData;
  questions: Question[];
  concept_map: ConceptMap;
}

// frontend/src/types/evaluation.ts
export interface MCQResult {
  question_id: number;
  selected: AnswerKey;
  is_correct: boolean;
  correct_answer: AnswerKey;
  explanation: string;
  next_difficulty: Difficulty;
}

export interface DimensionScore { key: string; label: string; score: number; weight: number; }

export interface VoiceResult {
  question_id: number;
  student_answer: string;
  dimension_scores: DimensionScore[];
  weighted_score: number;
  narrative_debrief: string;
  verdict: string;
  verdict_type: "success" | "info" | "warning" | "error";
  follow_up_question?: string;
  study_recommendations: string[];
}

export interface SessionResults {
  mcq_results: MCQResult[];
  voice_results: VoiceResult[];
  topic_scores: Record<string, { correct: number; total: number; avg_voice?: number }>;
  overall_mcq_pct: number;
  overall_voice_score: number;
}

// frontend/src/types/ui.ts
export type FlashType = "success" | "error" | "warning" | "info";

export interface FlashMessage {
  id: string;           // uuid for keying React list
  type: FlashType;
  content: string;
  dismissible: boolean;
  autoDismissMs?: number;
}
```

---

## 8. Provider Abstraction Implementation

### 8.1 LLM Provider Base

```python
# backend/providers/llm/base.py

from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class LLMMessage:
    role: str   # "system" | "user" | "assistant"
    content: str

@dataclass
class LLMResponse:
    content: str
    model: str
    provider: str
    prompt_tokens: int | None = None
    completion_tokens: int | None = None

class BaseLLMProvider(ABC):
    """All LLM providers implement this interface.
    The services layer only knows about this class — never about specific providers.
    """

    @abstractmethod
    async def complete(
        self,
        messages: list[LLMMessage],
        temperature: float | None = None,
        max_tokens: int | None = None,
        response_format: dict | None = None,   # e.g., {"type": "json_object"}
    ) -> LLMResponse:
        """Send messages, return a single complete response."""
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        pass
```

### 8.2 OpenAI-Compatible Provider (Ollama + LM Studio + OpenAI)

```python
# backend/providers/llm/openai_compatible.py
# This single class handles Ollama, LM Studio, and OpenAI because they all
# expose the same v1/chat/completions endpoint format.

import os
from openai import AsyncOpenAI
from .base import BaseLLMProvider, LLMMessage, LLMResponse
from core.config import AppConfig

class OpenAICompatibleProvider(BaseLLMProvider):
    """
    Covers:
    - Ollama: base_url=http://localhost:11434/v1, api_key="ollama" (any string)
    - LM Studio: base_url=http://localhost:1234/v1, api_key="lm-studio"
    - OpenAI: base_url=https://api.openai.com/v1, api_key=real key
    """

    def __init__(self, config: AppConfig):
        self.config = config
        provider = config.llm.provider
        
        # Resolve base_url and api_key per provider subsection
        if provider == "ollama":
            base_url = config.llm.ollama.base_url + "/v1"
            api_key = "ollama"
        elif provider == "lmstudio":
            base_url = config.llm.lmstudio.base_url
            api_key = config.llm.lmstudio.api_key
        elif provider == "openai":
            base_url = config.llm.openai.base_url
            api_key = config.llm.api_key or os.environ.get("OPENAI_API_KEY")
        else:
            raise ValueError(f"Unknown OpenAI-compatible provider: {provider}")

        self.client = AsyncOpenAI(base_url=base_url, api_key=api_key)
        self.model = config.llm.model
        self._provider = provider

    async def complete(self, messages, temperature=None, max_tokens=None, response_format=None):
        kwargs = {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature or self.config.llm.temperature,
            "max_tokens": max_tokens or self.config.llm.max_tokens,
        }
        if response_format:
            kwargs["response_format"] = response_format

        response = await self.client.chat.completions.create(**kwargs)
        return LLMResponse(
            content=response.choices[0].message.content,
            model=response.model,
            provider=self._provider,
            prompt_tokens=response.usage.prompt_tokens if response.usage else None,
            completion_tokens=response.usage.completion_tokens if response.usage else None,
        )

    def get_provider_name(self): return self._provider
    def get_model_name(self): return self.model
```

### 8.3 Provider Factory

```python
# backend/providers/llm/factory.py

from core.config import AppConfig
from .base import BaseLLMProvider
from .openai_compatible import OpenAICompatibleProvider
from .anthropic_provider import AnthropicProvider
from .gemini_provider import GeminiProvider
from .langchain_provider import LangChainProvider

def create_llm_provider(config: AppConfig) -> BaseLLMProvider:
    """
    Factory: reads config.llm.provider, returns the correct implementation.
    Adding a new provider = add one file + one elif here.
    """
    provider = config.llm.provider.lower()

    if provider in ("ollama", "lmstudio", "openai"):
        return OpenAICompatibleProvider(config)
    elif provider == "anthropic":
        return AnthropicProvider(config)
    elif provider == "gemini":
        return GeminiProvider(config)
    elif provider == "langchain":
        return LangChainProvider(config)
    else:
        raise ValueError(
            f"Unknown LLM provider '{provider}'. "
            f"Valid options: ollama, lmstudio, openai, anthropic, gemini, langchain"
        )
```

### 8.4 STT Provider Base + Factory Pattern

Follow identical pattern to LLM providers:

```python
# backend/providers/stt/base.py

from abc import ABC, abstractmethod

class BaseSTTProvider(ABC):
    @abstractmethod
    async def transcribe(self, audio_bytes: bytes, filename: str) -> dict:
        """Returns: { transcript: str, duration_seconds: float, language: str }"""
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        pass

# backend/providers/stt/factory.py

def create_stt_provider(config: AppConfig) -> BaseSTTProvider:
    provider = config.speech_to_text.provider.lower()
    if provider == "whisper_local":
        return WhisperLocalProvider(config)
    elif provider == "openai_whisper":
        return OpenAIWhisperProvider(config)
    elif provider == "aws_transcribe":
        return AWSTranscribeProvider(config)
    elif provider == "google_stt":
        return GoogleSTTProvider(config)
    else:
        raise ValueError(f"Unknown STT provider: {provider}")
```

---

## 9. API Endpoints

All endpoints prefixed with `/api`.

```
GET  /api/health
     → HealthResponse

GET  /api/config/ui
     → UIConfigResponse (safe subset of config for frontend)

POST /api/analyze
     Body: AnalyzeRequest (JSON)
     → AnalyzeResponse
     Side effect: stores session in SessionStore

POST /api/transcribe
     Body: FormData { audio: File (webm/wav/mp4) }
     → TranscribeResponse

POST /api/evaluate/mcq
     Body: MCQEvaluateRequest (JSON)
     → MCQEvaluationResponse
     Side effect: records answer + updates adaptive difficulty

POST /api/evaluate/voice
     Body: VoiceEvaluateRequest (JSON)
     → VoiceEvaluationResponse
     Side effect: records evaluation in session

GET  /api/sessions
     → { sessions: List[SessionMeta] }

GET  /api/session/{session_id}
     → { session: SessionMeta, results: SessionResults | None }
```

**Error format (all endpoints):**
```json
{ "detail": "Human readable error", "code": "PROVIDER_UNAVAILABLE", "hint": "Check that Ollama is running at localhost:11434" }
```

---

## 10. Prompt Templates (Jinja2)

All templates go in `backend/prompts/`. Use `{{ variable }}` syntax.
Templates have access to all evaluation config variables automatically via PromptManager.

### 10.1 summary_system.j2
```
You are an expert educational analyst. Analyse the following classroom session transcript and return ONLY valid JSON with no markdown, no explanation, no code fences.

Return this exact JSON structure:
{
  "session_title": "descriptive title inferred from content",
  "topics_covered": ["list", "of", "main", "topics"],
  "key_concepts": [
    { "concept": "name", "explanation": "one clear sentence", "topic": "which topic above" }
  ],
  "learning_objectives": ["Students will be able to...", "Students will understand..."],
  "teacher_insight": "2-3 sentences about teaching focus, style, and key emphases of this session",
  "confusion_zones": [
    {
      "topic": "topic name",
      "signal_type": "student_question|teacher_repeated|explicit_check|silence",
      "description": "what confused students and why",
      "timestamp_approx": "HH:MM if discernible from transcript, else null"
    }
  ]
}

Strict rules:
- Base EVERYTHING strictly on the transcript content
- confusion_zones: identify moments where students asked questions, where the teacher rephrased or repeated, or where "does everyone understand?" appears
- DO NOT invent topics or concepts not in the transcript
- session_title should be specific, not generic
```

### 10.2 questions_system.j2
```
You are an expert educational assessment designer. Based on the session summary and transcript, generate assessment questions and return ONLY valid JSON.

Session topics: {{ topics | join(', ') }}

{% if bloom_enabled %}
Use Bloom's Taxonomy levels. Distribute questions as:
{% for level, pct in bloom_distribution.items() %}
- {{ level }} ({{ (pct * 100)|int }}%): {{ (pct * total_questions)|round|int }} questions
{% endfor %}
{% endif %}

Generate {{ mcq_count }} MCQ questions and {{ tib_count }} "teach it back" questions.

MCQ difficulty target: {{ difficulty_distribution.easy*100|int }}% easy, {{ difficulty_distribution.medium*100|int }}% medium, {{ difficulty_distribution.hard*100|int }}% hard

Return this exact JSON:
{
  "questions": [
    {
      "id": 1,
      "type": "mcq",
      "topic": "exact topic from session",
      "difficulty": "easy|medium|hard",
      "bloom_level": "remember|understand|apply|analyze|evaluate",
      "question": "Question text?",
      "options": [
        {"key": "A", "text": "option text"},
        {"key": "B", "text": "option text"},
        {"key": "C", "text": "option text"},
        {"key": "D", "text": "option text"}
      ],
      "correct_answer": "A",
      "explanation": "Why this is correct (1-2 sentences)."
    },
    {
      "id": 6,
      "type": "teach_it_back",
      "topic": "exact topic from session",
      "difficulty": "medium",
      "bloom_level": "understand|apply|analyze",
      "question": "Explain [concept] as if teaching it to someone seeing it for the first time...",
      "evaluation_rubric": "A strong answer should include: (1) core definition, (2) how it works mechanically, (3) a concrete example or analogy, (4) why it matters"
    }
  ]
}

Rules:
- All questions MUST be answerable from the session content only
- MCQ distractors must be plausible but clearly wrong on reflection
- teach_it_back questions should come from confusion_zones if available
- No duplicate concepts across questions
- evaluation_rubric tells the AI evaluator what a complete answer requires
```

### 10.3 evaluate_voice_system.j2
```
You are {{ interviewer_name }}. {{ interviewer_persona }}

Your style: {{ interviewer_style }}
Domain: {{ interviewer_domain }}

The student was asked: "{{ question }}"

The evaluation rubric for this question is:
{{ evaluation_rubric }}

The student's answer ({{ "spoken and transcribed" if was_voice else "typed" }}):
"{{ student_answer }}"

Session context (what was taught in this class):
{{ session_context }}

Evaluate the student's answer and return ONLY valid JSON:
{
  "dimension_scores": [
    {% for dim in score_dimensions %}
    { "key": "{{ dim.key }}", "label": "{{ dim.label }}", "score": <integer 1-5>, "weight": {{ dim.weight }} }{% if not loop.last %},{% endif %}
    {% endfor %}
  ],
  "narrative_debrief": "Paragraph 1: What the student did well — be specific, quote their words.\n\nParagraph 2: What was missing or incorrect — name the exact concept, term, or mechanism they missed. Never be vague.\n\nParagraph 3: Actionable next steps — what specifically should they study, practice, or re-read?",
  "verdict": "{{ verdicts | map(attribute='label') | join(' | ') }}",
  "follow_up_question": "One natural follow-up question an interviewer would ask next",
  "study_recommendations": ["specific recommendation 1", "specific recommendation 2", "specific recommendation 3"]
}

Scoring rules:
- Score 5: Complete, accurate, with examples and connections. Interview-ready.
- Score 4: Mostly correct, minor gaps. Close to interview-ready.
- Score 3: Core idea present but missing important details or precision.
- Score 2: Partial understanding. Key mechanisms missing or confused.
- Score 1: Fundamental misunderstanding or very incomplete.

CRITICAL: Quote the student's actual words in paragraph 1 and 2. Generic feedback is not acceptable.
```

### 10.4 concept_map_system.j2
```
Generate a Mermaid.js concept map for the following session topics and concepts.

Topics: {{ topics | join(', ') }}
Key concepts: {{ concepts | join(', ') }}

Return ONLY a valid Mermaid flowchart in {{ direction }} direction showing:
1. How concepts relate to and depend on each other
2. Which concepts are prerequisites for others
3. The main topic as the root node

Use this exact format:
graph {{ direction }}
    A["Main Topic"] --> B["Sub-concept 1"]
    A --> C["Sub-concept 2"]
    B --> D["Detail 1"]
    ...

Rules:
- Maximum {{ max_nodes }} nodes
- Use double quotes around all node labels
- Node IDs must be single letters or short alphanumeric codes
- Show dependency direction: prerequisite --> dependent
- Keep labels concise (max 4 words)
- Return ONLY the mermaid code, nothing else
```

### 10.5 evaluate_mcq_system.j2
```
The student answered a multiple choice question.

Question: {{ question }}
Options: A) {{ option_a }} B) {{ option_b }} C) {{ option_c }} D) {{ option_d }}
Correct answer: {{ correct_answer }}
Student selected: {{ selected_answer }}
Difficulty: {{ difficulty }}
Hint level used: {{ hint_level }} of 3

Return ONLY valid JSON:
{
  "is_correct": true|false,
  "explanation": "1-2 sentences explaining why the correct answer is right",
  "next_difficulty": "easy|medium|hard",
  "hint": "If wrong and hint_level < 3: a helpful hint without giving away the answer. Otherwise null."
}

For next_difficulty:
- If correct at hard → stay hard
- If correct at medium → move to hard  
- If correct at easy → move to medium
- If wrong at hard → move to medium
- If wrong at medium or easy → move to easy
```

---

## 11. Frontend Architecture

### 11.1 App Shell (CloudScape AppLayout)

```
AppLayout
├── navigation (slot) → SessionSidebar (SideNavigation)
│     Items: [Home] [Session History] [Settings]
│     Sections: Recent Sessions (list of SessionMeta items)
│
├── notifications (slot) → Flashbar
│     Success: "Session analyzed", Error: "Provider unavailable"
│
├── content (slot) → Wizard component
│     Step 1: Input page
│     Step 2: Summary + Concept Map
│     Step 3: Assessment
│     Step 4: Results
│
└── tools (slot) → Help panel (optional Phase 2)
```

### 11.2 Wizard Step Configuration

```typescript
const steps = [
  {
    title: "Upload transcript",
    description: "Paste or upload your class transcript",
    content: <InputPage />,
    isOptional: false,
  },
  {
    title: "Session summary",
    description: "Review what was covered and the concept map",
    content: <SummaryPage />,
    isOptional: false,
  },
  {
    title: "Assessment",
    description: "MCQ + teach-it-back interview questions",
    content: <AssessmentPage />,
    isOptional: false,
  },
  {
    title: "Your results",
    description: "Detailed interview debrief and insights",
    content: <ResultsPage />,
    isOptional: false,
  },
];
```

### 11.3 State Management

Use React Context + useReducer for global session state. No Redux.

```typescript
// Global state shape
interface AppState {
  sessionId: string | null;
  studentName: string;
  analyzeResult: AnalyzeResult | null;
  currentQuestionIndex: number;
  currentDifficulty: Difficulty;
  mcqResults: Record<number, MCQResult>;
  voiceResults: Record<number, VoiceResult>;
  ui: {
    isAnalyzing: boolean;
    isTranscribing: boolean;
    isEvaluating: boolean;
    flashMessages: FlashMessage[];
  };
}
```

### 11.4 VoiceRecorder Component Behaviour

```
State machine:
idle → recording → transcribing → review → submitted

idle:        Show microphone button
recording:   Show waveform animation + timer + Stop button
             (MediaRecorder captures audio chunks → blob)
transcribing: Show Spinner "Transcribing with Whisper..."
             POST /api/transcribe with audio blob
review:      Show transcript in editable Textarea
             "Is this correct? Edit if needed." + Confirm button
submitted:   Transcript locked, POST /api/evaluate/voice
```

### 11.5 Adaptive Difficulty Hook

```typescript
// hooks/useAdaptiveDifficulty.ts
// Reads initial difficulty from API config
// Updates per-topic difficulty after each MCQ result
// Exposes: currentDifficulty, topicDifficulties, updateAfterAnswer()
```

---

## 12. Detailed Task List (Phase 0 — Tomorrow)

Execute in this exact order. Do not skip steps.

### TASK GROUP 1: Project Scaffold

- [ ] T01: Create root directory `distill/` with `README.md`, `.gitignore`, `Makefile`, `.env.example`
- [ ] T02: Create `config.yaml` and `config.example.yaml` with full schema from Section 5
- [ ] T03: Create `backend/` directory with `requirements.txt` listing all deps from Section 3
- [ ] T03b: Create `backend/pyproject.toml` with project metadata (name: distill-backend, python >=3.11), ruff config (line-length 100, target-version py311), and black config (line-length 100)
- [ ] T04: Create `frontend/` directory, run `npm create vite@latest . -- --template react-ts`
- [ ] T05: Install CloudScape: `npm install @cloudscape-design/components @cloudscape-design/global-styles @cloudscape-design/design-tokens`
- [ ] T06: Install other frontend deps: `npm install axios mermaid react-router-dom @types/react @types/node`
- [ ] T07: Write `Makefile` with targets: `dev-backend`, `dev-frontend`, `dev` (runs both), `install`, `test`, `lint`, `pull-model`
- [ ] T07b: Create `data/.gitkeep` so the SQLite directory is tracked by git but its contents are not (add `data/*.db` to `.gitignore`)

### TASK GROUP 2: Backend Core

- [ ] T08: Write `backend/core/config.py` — loads `config.yaml` via PyYAML, maps to typed dataclass hierarchy. Support env var overrides using `os.environ.get()`. Export singleton `get_config()`.
- [ ] T09: Write `backend/core/logging.py` — configure structlog with log level from config
- [ ] T10: Write `backend/core/exceptions.py` — define `ProviderError`, `TranscriptionError`, `EvaluationError`. Write FastAPI exception handlers that return `{"detail": ..., "code": ..., "hint": ...}`
- [ ] T11: Write `backend/core/prompt_manager.py` — Jinja2 Environment loading from `config.prompts.directory`. `render(template_key, **kwargs)` method. Inject evaluation config vars automatically.

### TASK GROUP 3: LLM Providers

- [ ] T12: Write `backend/providers/llm/base.py` — `LLMMessage`, `LLMResponse` dataclasses, `BaseLLMProvider` ABC with `complete()` and `get_provider_name()`, `get_model_name()` abstract methods
- [ ] T13: Write `backend/providers/llm/openai_compatible.py` — handles Ollama, LM Studio, OpenAI using `AsyncOpenAI` client. Read base_url and api_key per provider subsection.
- [ ] T14: Write `backend/providers/llm/anthropic_provider.py` — uses `anthropic.AsyncAnthropic`. Extract system message from messages list. Map to Anthropic's format.
- [ ] T15: Write `backend/providers/llm/gemini_provider.py` — uses `google.generativeai`. Convert messages to Gemini format.
- [ ] T16: Write `backend/providers/llm/langchain_provider.py` — wraps any backend using LangChain. Read `config.llm.langchain.backend` to choose which chain to build.
- [ ] T17: Write `backend/providers/llm/factory.py` — `create_llm_provider(config)` returns correct implementation based on `config.llm.provider`
- [ ] T18: Write integration test for each provider: send a simple "Say hello" message, verify non-empty string response

### TASK GROUP 4: STT Providers

- [ ] T19: Write `backend/providers/stt/base.py` — `BaseSTTProvider` ABC with `transcribe(audio_bytes, filename)` returning `{transcript, duration_seconds, language}`
- [ ] T20: Write `backend/providers/stt/whisper_local.py` — load Whisper model (size from config) on startup. `transcribe()` saves temp file, runs model, returns result. Log model load time.
- [ ] T21: Write `backend/providers/stt/openai_whisper.py` — uses OpenAI Audio API
- [ ] T22: Write `backend/providers/stt/aws_transcribe.py` — stub with clear TODO for Phase 2
- [ ] T23: Write `backend/providers/stt/factory.py` — same pattern as LLM factory

### TASK GROUP 5: Prompt Templates

- [ ] T24: Write `backend/prompts/summary_system.j2` from Section 10.1
- [ ] T25: Write `backend/prompts/questions_system.j2` from Section 10.2
- [ ] T26: Write `backend/prompts/concept_map_system.j2` from Section 10.4
- [ ] T27: Write `backend/prompts/evaluate_mcq_system.j2` from Section 10.5
- [ ] T28: Write `backend/prompts/evaluate_voice_system.j2` from Section 10.3
- [ ] T29: Write `backend/prompts/confusion_map_system.j2`
  - DISTINCT purpose from summary_system.j2: this template is used POST-QUIZ (not during analysis)
  - It re-analyses the confusion_zones from the summary PLUS the student's actual quiz results to produce a ranked list of concepts to prioritise for study
  - Input: confusion_zones list + mcq_results + voice_results
  - Output: JSON with `{ prioritised_review: [{topic, reason, urgency: high|medium|low}] }`
  - This powers the "What to study next" section on ResultsPage

### TASK GROUP 6: Services

- [ ] T30: Write `backend/services/analyzer.py` — `TranscriptAnalyzer` class
  - `__init__(llm: BaseLLMProvider, prompt_mgr: PromptManager, config: AppConfig)`
  - `async analyze(transcript: str) -> tuple[SummaryResponse, ConceptMapResponse]`
  - Calls LLM twice: once for summary, once for concept map
  - Parses JSON responses with error handling (retry on JSON parse failure)

- [ ] T31: Write `backend/services/assessor.py` — `QuestionGenerator` class
  - `__init__(llm, prompt_mgr, config)`
  - `async generate(summary: SummaryResponse, transcript: str) -> list[Question]`
  - Generates MCQ + teach_it_back questions per config counts
  - Validates question count and format

- [ ] T32: Write `backend/services/evaluator.py` — `AnswerEvaluator` class
  - `__init__(llm, prompt_mgr, config)`
  - `async evaluate_mcq(question, selected, session_ctx) -> MCQEvaluationResponse`
  - `async evaluate_voice(question, student_answer, session_ctx, was_voice) -> VoiceEvaluationResponse`
  - Both parse JSON LLM responses, compute weighted scores, determine verdict

### TASK GROUP 7: Session Storage

- [ ] T33: Write `backend/storage/base.py` — `BaseSessionStore` ABC
  - Methods: `save_session()`, `get_session()`, `list_sessions()`, `update_results()`
- [ ] T34: Write `backend/storage/memory_store.py` — dict-based in-memory store. Thread-safe with asyncio.Lock. Capped at `config.session.max_sessions_in_memory`.

### TASK GROUP 8: Routers

- [ ] T35: Write `backend/routers/system.py` — `GET /api/health` and `GET /api/config/ui`. Health checks LLM provider with a lightweight test call.
- [ ] T36: Write `backend/routers/analyze.py` — `POST /api/analyze`
  - Validate request
  - Call `analyzer.analyze()` → summary + concept_map
  - Call `assessor.generate()` → questions
  - Store session
  - Return `AnalyzeResponse`
- [ ] T37: Write `backend/routers/transcribe.py` — `POST /api/transcribe`
  - Accept multipart audio file
  - Call `stt_provider.transcribe()`
  - Return transcript
- [ ] T38: Write `backend/routers/evaluate.py` — `POST /api/evaluate/mcq` and `POST /api/evaluate/voice`
  - Load session for context
  - Call evaluator service
  - Update session with result
  - Return evaluation
- [ ] T39: Write `backend/routers/sessions.py` — `GET /api/sessions` and `GET /api/session/{id}`

### TASK GROUP 9: Main App + Dependency Injection

- [ ] T40: Write `backend/main.py`
  - Create FastAPI app
  - Load config once at startup via `lifespan` context manager
  - Initialize providers, services, storage as singletons
  - Register all routers with `/api` prefix
  - Add CORS middleware using `config.server.cors_origins`
  - Add global exception handlers
  - Log startup info: provider name, model, STT provider, listening address

### TASK GROUP 10: Frontend — Foundation

- [ ] T40b: Write `frontend/src/context/AppContext.tsx`
  - Define `AppState` interface (sessionId, studentName, analyzeResult, currentQuestionIndex, currentDifficulty, mcqResults, voiceResults, ui with isAnalyzing/isTranscribing/isEvaluating/flashMessages)
  - Define `AppAction` discriminated union (SET_ANALYZE_RESULT, SET_MCQ_RESULT, SET_VOICE_RESULT, ADVANCE_QUESTION, ADD_FLASH, DISMISS_FLASH, RESET)
  - Write `appReducer(state, action) → AppState` — pure function, no side effects
  - Export `AppContext`, `AppProvider` (wraps children with Context.Provider), `useAppState()` and `useAppDispatch()` custom hooks

- [ ] T41: Write `frontend/src/config/api.ts` — axios instance with `baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000'`. Add request/response interceptors for error handling.
- [ ] T42: Write `frontend/src/types/` — all TypeScript interfaces from Section 7.2
- [ ] T43: Write `frontend/src/api/` — typed async functions for each endpoint. Each function throws typed errors on failure.
- [ ] T44: Write `frontend/src/App.tsx` — import CloudScape global styles, set up React Router, wrap with AppShell
- [ ] T45: Write `frontend/src/components/layout/AppShell.tsx`
  - CloudScape `AppLayout` + `TopNavigation` + `SessionSidebar`
  - `TopNavigation`: brand name from API config, no user menu for Phase 0
  - `AppLayout` content area renders `<Outlet />` from React Router

### TASK GROUP 11: Frontend — Pages

- [ ] T46: Write `frontend/src/pages/InputPage.tsx`
  - CloudScape `Container` with `Header`
  - `FormField` + `Textarea` for transcript (min-height: 300px)
  - `FormField` + `Input` for student name
  - `FormField` + `FileUpload` for .txt / .vtt file drag-drop
  - `Button` variant="primary" "Analyze Transcript →"
  - Show `Spinner` during analysis

- [ ] T47: Write `frontend/src/pages/SummaryPage.tsx`
  - `ColumnLayout` (3 cols) stat cards: Topics count, Concepts count, Confusion zones count
  - `SplitPanel`: left = session summary, right = concept map
  - Left: `Container` with topics as `Badge`, key concepts as `ExpandableSection`, objectives as `List`
  - Right: `ConceptMap` component (Mermaid renderer)
  - Below: confusion zones as `Alert` components with `type="warning"`

- [ ] T48: Write `frontend/src/pages/AssessmentPage.tsx`
  - Top: `ProgressBar` showing current question / total (e.g. "Question 4 of 8")
  - Below progress: `Badge` showing question type ("Multiple Choice" or "Teach It Back") and difficulty
  - Sequentially renders ONE question at a time — NO tabs (questions arrive in fixed adaptive order)
  - If current question type is `mcq`: render `MCQQuestion` component
  - If current question type is `teach_it_back`: render `TeachItBack` component
  - "Next" button advances to next question; after last question navigates to ResultsPage
  - Handles question sequencing and difficulty updating via `useAdaptiveDifficulty` hook

- [ ] T49: Write `frontend/src/pages/ResultsPage.tsx`
  - Overall score stat cards (MCQ + Voice)
  - `Table` of topic scores (sortable)
  - `ExpandableSection` per teach-it-back question — collapsed shows verdict badge, expanded shows full debrief
  - `WhatsAppExport` component with `CopyToClipboard` button
  - "Retake" and "New Transcript" buttons

### TASK GROUP 12: Frontend — Components

- [ ] T50: Write `frontend/src/components/assessment/MCQQuestion.tsx`
  - Show question with `BloomLevel` and `DifficultyBadge`
  - `RadioGroup` for options A/B/C/D (full width buttons with letter prefix)
  - After submit: `Alert` success/error with explanation
  - Hint system: "Need a hint?" button reveals hint text progressively

- [ ] T51: Write `frontend/src/components/assessment/VoiceRecorder.tsx`
  - Uses `MediaRecorder` API. Captures WebM audio.
  - States: idle → recording → transcribing → review
  - `recording`: animated waveform bars (CSS) + countdown timer + Stop button
  - `transcribing`: `Spinner` + "Transcribing with Whisper…"
  - `review`: `Textarea` showing transcript (editable) + Confirm button
  - Error state: "Microphone access denied" → show text fallback

- [ ] T52: Write `frontend/src/components/assessment/TeachItBack.tsx`
  - `Toggle` for voice/text mode
  - Renders `VoiceRecorder` or `Textarea` based on mode
  - Shows `evaluationRubric` as collapsed hint
  - Submit button (disabled until answer has min words)

- [ ] T53: Write `frontend/src/components/summary/ConceptMap.tsx`
  - Takes `mermaid_syntax: string` prop
  - Uses `mermaid.render()` to generate SVG
  - Displays in iframe-safe container
  - After quiz: update node colors based on performance (green/amber/red)

- [ ] T54: Write `frontend/src/components/results/InterviewDebrief.tsx`
  - `ExpandableSection` header: question number + verdict `StatusIndicator` + one-line summary
  - Expanded body: 3 paragraphs of narrative, dimension scores as small `ProgressBar` rows, follow-up question in `Alert info`

- [ ] T55: Write `frontend/src/components/results/WhatsAppExport.tsx`
  - Formats session result as WhatsApp-friendly text
  - Uses brand name from config (fetch from `/api/config/ui`)
  - `CopyToClipboard` button with success toast

### TASK GROUP 13: Hooks

- [ ] T55b: Write `frontend/src/hooks/useSession.ts`
  - Wraps `useAppState` + `useAppDispatch`
  - Exposes: `sessionId`, `analyzeResult`, `submitTranscript(transcript, studentName)`, `resetSession()`
  - `submitTranscript()` calls `POST /api/analyze`, dispatches `SET_ANALYZE_RESULT`, adds flash on error

- [ ] T56: Write `frontend/src/hooks/useVoiceRecorder.ts`
  - Manages MediaRecorder lifecycle
  - Exposes: `state`, `startRecording()`, `stopRecording()`, `audioBlob`, `reset()`
  - Handles `getUserMedia` permission errors gracefully

- [ ] T57: Write `frontend/src/hooks/useAdaptiveDifficulty.ts`
  - Initialized with `config.assessment.adaptive_engine` from API
  - `updateAfterAnswer(topic, isCorrect)` → updates per-topic difficulty
  - Exposes: `currentDifficulty(topic)`, `overallDifficulty`

### TASK GROUP 14: Documentation

- [ ] T58: Write `README.md` with:
  - What Distill does (3 sentences)
  - Prerequisites checklist (Node, Python, Ollama/LM Studio)
  - Step-by-step setup: config.yaml, .env, model pull, install
  - Two-command run: `make dev-backend` + `make dev-frontend`
  - Provider switch guide (one-line config changes for each provider)
  - Architecture overview (link to ARCHITECTURE.md)

- [ ] T59: Write `ARCHITECTURE.md` with full architecture diagram (ASCII) and design decisions

- [ ] T60: Write `CONTRIBUTING.md` with: how to add a new LLM provider (5 steps), how to add a new STT provider, how to modify prompts, coding standards

---

## 13. Phase 1+ Roadmap (for future Claude Code sessions)

**Phase 1 — Multi-student + Persistence**
- Replace memory store with SQLite store
- Add student join codes
- Teacher dashboard (aggregate results per question)
- Session history with learning trajectory chart
- Flashcard export (Anki CSV from wrong MCQ answers)
- WhatsApp bot integration for quiz sharing

**Phase 2 — Cloud Deployment**
- Swap Whisper local → AWS Transcribe (change one line in config.yaml)
- Swap Ollama → AWS Bedrock Llama (change one line in config.yaml)
- Deploy FastAPI on AWS Lambda (container) + API Gateway
- Deploy React on AWS Amplify or Vercel
- Add Supabase for auth + PostgreSQL session storage
- PDF report generation
- AI study partner (post-quiz chat using session as context)

**Phase 3 — SaaS**
- Multi-tenant PostgreSQL
- Stripe payment tiers
- Institution accounts + class management
- LMS integration (Moodle, Canvas) via LTI
- Mobile-responsive UI (CloudScape is already responsive)
- White-label support (brand config per tenant)

---

## 14. Key Design Principles (Never Violate)

1. **Zero hardcoding.** No model names, URLs, API keys, prompt text, or thresholds in Python or TypeScript. Everything in config.yaml or env vars.

2. **Provider-agnostic services.** Services (analyzer, assessor, evaluator) only know about `BaseLLMProvider`. They never import `OpenAICompatibleProvider` directly.

3. **Prompts are data, not code.** All prompt text lives in `.j2` template files. Changing a prompt never requires a code change or restart (implement hot-reload of templates).

4. **Graceful degradation.** If voice fails, fall back to text. If LLM returns invalid JSON, retry up to `config.llm.retry_attempts` times with a clearer instruction. Never show a raw traceback to the student.

5. **Config-driven features.** Every feature can be enabled/disabled via `config.yaml` (e.g., `ui.features.voice_enabled: false` hides the recorder). No feature flags in code.

6. **Additive evolution.** Adding a new provider = one file + one elif in factory. No existing code changes. Adding a new assessment type = one new template + extend question schema.

---

## 15. Makefile

```makefile
.PHONY: dev dev-backend dev-frontend install install-backend install-frontend test lint

dev:
	make -j2 dev-backend dev-frontend

dev-backend:
	cd backend && uvicorn main:app --reload --host 0.0.0.0 --port 8000

dev-frontend:
	cd frontend && npm run dev

install: install-backend install-frontend

install-backend:
	cd backend && pip install -r requirements.txt

install-frontend:
	cd frontend && npm install

test:
	cd backend && pytest tests/ -v

lint:
	cd backend && ruff check . && black --check .
	cd frontend && npm run lint

pull-model:
	ollama pull $(MODEL)
```

---

## 16. Final Notes for Claude Code

- Start with Tasks T01–T07 (scaffold) before writing any logic
- Add a Vite dev proxy in `vite.config.ts` to forward `/api` calls to `localhost:8000` — without this, CORS blocks every API call during frontend development:
  ```ts
  server: { proxy: { '/api': { target: 'http://localhost:8000', changeOrigin: true } } }
  ```
- Write `core/config.py` before any provider — everything depends on it
- Test each provider individually (T18) before wiring into services
- The Whisper model loads slowly on first use — log a clear message so students know to wait
- All JSON parsing from LLM should be wrapped in try/except with a retry that adds "Return ONLY valid JSON, no other text" to the prompt
- CloudScape requires the global styles import in `main.tsx`: `import '@cloudscape-design/global-styles/index.css'`
- The Mermaid renderer needs `mermaid.initialize({ startOnLoad: false })` in a useEffect, then call `mermaid.render()` imperatively
- For the VoiceRecorder, request audio with `{ audio: { channelCount: 1, sampleRate: 16000 } }` — Whisper prefers 16kHz mono
- Use `structuredClone()` for immutable state updates in the React reducer
```
