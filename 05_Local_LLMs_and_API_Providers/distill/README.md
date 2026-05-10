# Distill — Pure knowledge, every class

> An AI-powered classroom assessment tool by Inceptez.  
> Paste a transcript → get a concept map + adaptive quiz + Dr. Priya's interview debrief.

---

## What It Does

Distill turns any Teams / Zoom / Google Meet transcript into a complete learning assessment in minutes:

1. **Analyzes the transcript** — map-reduce summarization extracts topics, key concepts, and a structured summary
2. **Draws a concept map** — Mermaid diagram showing how every concept connects
3. **Generates an adaptive quiz** — 5 MCQ questions (difficulty adjusts per answer) + 3 Teach-It-Back voice questions
4. **Evaluates every answer** — MCQ explanations + Dr. Priya's AI interview debrief across 5 dimensions
5. **Exports results** — WhatsApp-ready report with score, verdict, and study recommendations

All processing happens locally. No data leaves your machine when using Ollama or LM Studio.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          Browser (localhost:5173)                   │
│                                                                     │
│  InputPage → SummaryPage → AssessmentPage → ResultsPage            │
│  React 18 + AWS CloudScape UI + React Router v6                    │
│                                                                     │
│  State: useReducer (AppContext) — no Redux, no Zustand             │
│  SSE streaming: fetch() + ReadableStream (not EventSource)         │
└──────────────────────────────┬──────────────────────────────────────┘
                               │ HTTP / SSE
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    FastAPI Backend (localhost:8000)                  │
│                                                                     │
│  Routers                                                            │
│  ├── POST /api/analyze/stream   → SSE: live progress + result      │
│  ├── POST /api/evaluate/mcq     → MCQ grading + explanation        │
│  ├── POST /api/evaluate/voice   → Dr. Priya debrief (5 dimensions) │
│  ├── POST /api/transcribe       → Whisper speech-to-text           │
│  ├── GET  /api/sessions         → Session list                     │
│  └── GET  /api/config/ui        → UI feature flags                 │
│                                                                     │
│  Services                                                           │
│  ├── Analyzer   — map-reduce summarization + concept map           │
│  ├── Assessor   — MCQ + Teach-It-Back question generation          │
│  └── Evaluator  — MCQ correctness + voice scoring                  │
│                                                                     │
│  Providers (swap via config.yaml — no code changes)                │
│  ├── LLM: Ollama │ LM Studio │ OpenAI │ Anthropic │ Gemini        │
│  └── STT: Whisper local │ OpenAI Whisper API                       │
│                                                                     │
│  Storage                                                            │
│  ├── memory  — in-process dict (default, lost on restart)         │
│  └── sqlite  — aiosqlite WAL, survives restarts                   │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│              LLM Server (Ollama :11434 or LM Studio :1234)          │
│              + Whisper medium model (cached after first download)   │
└─────────────────────────────────────────────────────────────────────┘
```

### Key Design Decisions

| Decision | Why |
|---|---|
| SSE over WebSocket | One-way server→client stream; simpler, no handshake overhead |
| `fetch()` not `EventSource` | `EventSource` doesn't support POST bodies; SSE over POST requires fetch |
| `stream=True` for local LLMs | LM Studio / Ollama kill idle connections at ~120 s; streaming keeps the socket alive |
| map-reduce distillation | Transcripts can be 100k+ chars; this fits any context window by chunking |
| SQLite WAL mode | Allows concurrent reads during writes — safe for multi-user local use |
| `key={question.id}` on MCQ | Forces React to unmount/remount per question — prevents stale state carrying over |

---

## Project Structure

```
distill/
├── README.md                    ← This file
├── config.yaml                  ← Master config — edit this to change everything
├── config.example.yaml          ← Safe reference copy (never edited)
├── .env                         ← API keys (never commit)
├── .env.example                 ← Template — copy to .env
├── Makefile                     ← make dev / make install / make test
│
├── prompts/                     ← Jinja2 prompt templates (edit to tune AI behavior)
│   ├── summary_system.j2        ← Topic extraction + structured summary
│   ├── concept_map_system.j2    ← Mermaid diagram generation
│   ├── questions_system.j2      ← MCQ + Teach-It-Back question generation
│   ├── evaluate_mcq_system.j2   ← MCQ grading + explanation
│   ├── evaluate_voice_system.j2 ← Dr. Priya 5-dimension interview scoring
│   └── confusion_map_system.j2  ← Confusion zone detection
│
├── backend/
│   ├── main.py                  ← FastAPI app factory, middleware, startup
│   ├── requirements.txt         ← Python dependencies
│   ├── data/
│   │   └── sessions.db          ← SQLite database (auto-created on first run)
│   │
│   ├── core/
│   │   ├── config.py            ← Pydantic settings loader (config.yaml + env vars)
│   │   ├── logging.py           ← structlog structured logging
│   │   ├── exceptions.py        ← DistillError, SessionNotFoundError, etc.
│   │   ├── prompt_manager.py    ← Jinja2 template renderer
│   │   └── utils.py             ← Shared helpers
│   │
│   ├── providers/
│   │   ├── llm/
│   │   │   ├── base.py          ← BaseLLMProvider, LLMMessage, LLMResponse
│   │   │   ├── openai_compatible.py  ← Ollama + LM Studio + OpenAI (one client)
│   │   │   ├── anthropic.py     ← Anthropic Claude
│   │   │   ├── gemini.py        ← Google Gemini
│   │   │   └── factory.py       ← create_llm_provider(config)
│   │   └── stt/
│   │       ├── base.py          ← BaseSTTProvider
│   │       ├── whisper_local.py ← Local openai-whisper (auto-downloads model)
│   │       ├── openai_whisper.py← OpenAI Whisper API
│   │       └── factory.py       ← create_stt_provider(config)
│   │
│   ├── services/
│   │   ├── analyzer.py          ← map-reduce distillation + concept map
│   │   ├── assessor.py          ← question generation
│   │   └── evaluator.py         ← MCQ + voice evaluation
│   │
│   ├── routers/
│   │   ├── analyze_stream.py    ← POST /api/analyze/stream (SSE)
│   │   ├── analyze.py           ← POST /api/analyze (non-streaming fallback)
│   │   ├── evaluate.py          ← POST /api/evaluate/mcq + /voice
│   │   ├── transcribe.py        ← POST /api/transcribe
│   │   ├── sessions.py          ← GET /api/sessions + /sessions/{id}
│   │   └── system.py            ← GET /api/config/ui + /api/providers
│   │
│   ├── storage/
│   │   ├── base.py              ← BaseSessionStore interface
│   │   ├── memory_store.py      ← In-memory (default)
│   │   ├── sqlite_store.py      ← SQLite (persistent, survives restarts)
│   │   └── factory.py           ← create_session_store(config)
│   │
│   ├── models/
│   │   ├── requests.py          ← Pydantic request schemas
│   │   └── responses.py         ← Pydantic response schemas
│   │
│   └── tests/
│       ├── conftest.py          ← pytest fixtures
│       ├── test_config.py       ← Config loading tests
│       ├── test_providers.py    ← LLM/STT provider tests
│       ├── test_services.py     ← Analyzer/Assessor/Evaluator tests
│       └── test_routers.py      ← API endpoint tests
│
└── frontend/
    ├── package.json
    ├── vite.config.ts           ← Vite dev server + proxy to :8000
    └── src/
        ├── main.tsx             ← React root, CloudScape theme
        ├── App.tsx              ← AppShell wrapper
        ├── router.tsx           ← React Router v6 routes
        │
        ├── pages/
        │   ├── InputPage.tsx    ← Step 1: transcript upload + live progress panel
        │   ├── SummaryPage.tsx  ← Step 2: topics + concept map
        │   ├── AssessmentPage.tsx ← Step 3: MCQ + Teach-It-Back wizard
        │   └── ResultsPage.tsx  ← Step 4: scores + Dr. Priya debrief + export
        │
        ├── components/
        │   ├── layout/
        │   │   ├── AppShell.tsx       ← Top nav + flash messages
        │   │   └── SessionSidebar.tsx ← Session history sidebar
        │   ├── assessment/
        │   │   ├── MCQQuestion.tsx    ← Radio group + hint system + feedback
        │   │   ├── TeachItBack.tsx    ← Voice recorder + text fallback + debrief
        │   │   ├── VoiceRecorder.tsx  ← MediaRecorder WebM capture
        │   │   └── DifficultyBadge.tsx
        │   ├── summary/
        │   │   ├── ConceptMap.tsx     ← Mermaid diagram renderer
        │   │   └── ConfusionZones.tsx ← Weak area highlights
        │   └── results/
        │       ├── InterviewDebrief.tsx ← Dr. Priya score breakdown
        │       └── WhatsAppExport.tsx   ← One-tap WhatsApp share
        │
        ├── api/
        │   ├── analyze.ts       ← SSE streaming + fetch-based client
        │   ├── evaluate.ts      ← MCQ + voice evaluation calls
        │   ├── transcribe.ts    ← Audio upload
        │   └── sessions.ts      ← Session list + detail
        │
        ├── context/
        │   └── AppContext.tsx   ← Global state: useReducer + Context
        │
        ├── hooks/
        │   ├── useSession.ts           ← Submit transcript, track progress
        │   ├── useVoiceRecorder.ts     ← MediaRecorder lifecycle
        │   └── useAdaptiveDifficulty.ts ← Per-topic difficulty tracking
        │
        └── types/
            ├── session.ts
            ├── assessment.ts
            ├── evaluation.ts
            └── ui.ts
```

---

## Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Python | 3.10+ | 3.10 from python.org recommended on macOS |
| Node.js | 20+ | LTS recommended |
| LM Studio **or** Ollama | latest | For local LLMs (free, no API key) |
| Microphone | — | For Teach-It-Back voice answers |

> **Cloud alternative:** If you don't want a local LLM server, you can use OpenAI, Anthropic, or Google Gemini — just set the API key in `.env` and change one line in `config.yaml`.

---

## Setup — LM Studio (Recommended for macOS)

LM Studio gives you a GUI to download and manage models, and runs the same OpenAI-compatible API.

### Step 1 — Install LM Studio

Download from [lmstudio.ai](https://lmstudio.ai) and install it.

### Step 2 — Download the model

Open LM Studio → **Discover** tab → search `qwen3-4b-2507` → download the **GGUF Q8_0** variant (~4.3 GB).

> **Important:** If both GGUF and MLX variants appear, download only the GGUF one. MLX requires a specific Python dylib that may not be present on all machines.

Or use the CLI after installing LM Studio:

```bash
lms server start
lms get qwen/qwen3-4b-2507    # downloads GGUF Q8_0
```

### Step 3 — Load the model with a large context window

```bash
lms load qwen/qwen3-4b-2507 --context-length 32768 -y
```

> **Why 32768?** The default context (4096) is too small for Distill's system prompts (~6000 tokens). 32k fits all prompts comfortably. Qwen3-4B supports up to 262k.

### Step 4 — Clone the repo and configure

```bash
cd distill
cp .env.example .env
# No edits needed — LM Studio is the default in config.yaml
```

### Step 5 — Install Python dependencies

```bash
# macOS: use the python.org Python 3.10 (not Homebrew)
/usr/local/bin/pip3 install -r backend/requirements.txt
```

### Step 6 — Fix SSL certificates (macOS Python 3.10 only, one-time)

```bash
"/Applications/Python 3.10/Install Certificates.command"
```

> This is required so Whisper can download its model on first use. Without it you get `SSLCertVerificationError`.

### Step 7 — Install frontend dependencies

```bash
cd frontend && npm install
```

### Step 8 — Run (two terminals)

**Terminal 1 — Backend:**
```bash
cd distill/backend
/usr/local/bin/python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 — Frontend:**
```bash
cd distill/frontend
npm run dev
```

### Step 9 — Open the app

Visit **http://localhost:5173**

---

## Setup — Ollama (Alternative)

### Step 1 — Install Ollama

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### Step 2 — Pull a model

```bash
ollama pull qwen2.5:7b        # recommended (7B, good balance)
# or: ollama pull llama3.2:3b  (smaller, faster on CPU)
# or: ollama pull gemma3:9b    (strong reasoning)
```

### Step 3 — Edit config.yaml

```yaml
llm:
  provider: "ollama"
  model: "qwen2.5:7b"
```

### Step 4 — Install and run

```bash
cp .env.example .env
make install
make dev   # starts backend + frontend together
```

---

## Setup — Cloud LLM (OpenAI / Anthropic / Gemini)

No local server needed. Just set the API key and update `config.yaml`.

### OpenAI

```yaml
# config.yaml
llm:
  provider: "openai"
  model: "gpt-4o-mini"
```
```bash
# .env
OPENAI_API_KEY=sk-...
```

### Anthropic Claude

```yaml
llm:
  provider: "anthropic"
  model: "claude-3-5-haiku-20241022"
```
```bash
ANTHROPIC_API_KEY=sk-ant-...
```

### Google Gemini

```yaml
llm:
  provider: "gemini"
  model: "gemini-2.0-flash"
```
```bash
GOOGLE_API_KEY=AIza...
```

---

## How to Use Distill

### Step 1 — Upload a transcript

Open http://localhost:5173.

- **Enter your name** (used in the assessment report)
- **Add a session label** (e.g. "Module 5 — RAG Basics") — optional
- **Paste a transcript** or upload a file:
  - `.txt` — plain text
  - `.vtt` — Zoom / Teams auto-generated captions
  - `.docx` — Word document
- Click **Analyze Transcript**

A live progress panel shows every step:

```
✓ 📄 Reading (175,827 chars loaded)
✓ ✂️  Splitting into 10 chunks
✓ 🔍 Summarizing chunk 1 of 10
  ...
✓ 🔗 Merging 10 chunk summaries
✓ 📝 Topics & Concepts
✓ 🗺️  Concept Map (19 nodes)
✓ 🎯 Quiz Questions (5 MCQ + 3 Teach-It-Back)
✓ 💾 Saving session
```

### Step 2 — Review the summary

The Summary page shows:
- **Session title** and **8 key topics**
- **Mermaid concept map** — click any node to explore
- **Confusion zones** — areas the model flagged as complex

Click **Start Assessment** to continue.

### Step 3 — Complete the assessment

**MCQ Questions (5 questions):**
- Select an answer from A / B / C / D
- Use "Need a hint?" (3 hint levels) if stuck
- Click **Submit Answer** — feedback appears immediately
- Click **Next Question**

Difficulty adapts: 2 correct in a row → harder; 1 wrong → easier.

**Teach-It-Back Questions (3 questions):**
- Read the question
- Click **Start Recording** and explain the concept in your own words (up to 2 minutes)
- Click **Stop Recording** — Whisper transcribes your answer
- Or use the **Type your answer** text fallback if microphone is unavailable
- Click **Submit** — Dr. Priya scores your answer across 5 dimensions

### Step 4 — View results

The Results page shows:
- **MCQ score** (e.g. 5/5 = 100%)
- **Per-question breakdown** with correct answers and explanations
- **Dr. Priya's debrief** for each voice answer:
  - Technical Accuracy (30%)
  - Conceptual Depth (25%)
  - Clarity of Explanation (20%)
  - Use of Examples (15%)
  - Concept Connections (10%)
- **Overall verdict**: Strong / Good / Developing / Foundational
- **Study recommendations** — 3 specific things to review

Click **Share on WhatsApp** to send your report.

---

## Configuration Reference

All settings are in `config.yaml`. Every value can be overridden by an environment variable: `DISTILL_<SECTION>_<KEY>=value`.

### LLM settings

```yaml
llm:
  provider: "lmstudio"            # ollama | lmstudio | openai | anthropic | gemini
  model: "qwen/qwen3-4b-2507"    # model identifier
  temperature: 0.3                # lower = more deterministic JSON output
  max_tokens: 2048                # 2k is plenty for structured JSON
  timeout_seconds: 180            # per-request timeout
  chunk_size_chars: 20000         # ~5k tokens per map-reduce chunk
  chunk_overlap_chars: 500        # overlap between chunks to preserve context
```

### Speech-to-text settings

```yaml
speech_to_text:
  provider: "whisper_local"       # whisper_local | openai_whisper
  language: "en"                  # transcription language

  whisper_local:
    model_size: "medium"          # tiny | base | small | medium | large
    device: "cpu"                 # cpu | cuda | mps
    download_on_startup: false    # true = download model when server starts
```

> **Model size guide:**
> - `tiny` — 75 MB, very fast, lower accuracy
> - `base` — 145 MB, fast, decent accuracy
> - `small` — 465 MB, good balance
> - `medium` — 1.5 GB, high accuracy (default)
> - `large` — 3 GB, best accuracy, slow on CPU

### Session storage

```yaml
session:
  storage: "sqlite"               # memory | sqlite
  sqlite_path: "./data/sessions.db"
  max_sessions_in_memory: 100     # only used when storage = memory
```

> Use `sqlite` to persist sessions across backend restarts. Use `memory` for demos.

### Assessment tuning

```yaml
assessment:
  mcq:
    count: 5                      # number of MCQ questions
    difficulty_distribution:
      easy: 0.30
      medium: 0.50
      hard: 0.20
    show_hints: true
    hint_levels: 3

  teach_it_back:
    count: 3                      # number of voice questions
    max_recording_seconds: 120
```

---

## Makefile Commands

```bash
make install          # install all backend + frontend dependencies
make dev              # start backend + frontend together (parallel)
make dev-backend      # start backend only (port 8000)
make dev-frontend     # start frontend only (port 5173)
make test             # run pytest test suite
make lint             # ruff + black (backend) + eslint (frontend)
make clean            # remove __pycache__, .pyc files
```

---

## API Reference

Once running, visit **http://localhost:8000/docs** for interactive Swagger UI.

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/analyze/stream` | Analyze transcript — SSE stream of progress events + final result |
| `POST` | `/api/evaluate/mcq` | Evaluate an MCQ answer |
| `POST` | `/api/evaluate/voice` | Evaluate a Teach-It-Back voice/text answer |
| `POST` | `/api/transcribe` | Transcribe audio (WebM/MP4/WAV) to text |
| `GET` | `/api/sessions` | List all sessions |
| `GET` | `/api/sessions/{id}` | Get session detail |
| `GET` | `/api/config/ui` | UI feature flags |
| `GET` | `/api/providers` | Active LLM + STT provider info |

### SSE event format

```
POST /api/analyze/stream
Content-Type: application/json

{ "transcript": "...", "student_name": "Priya", "session_label": "Module 5" }
```

Events arrive as `data: {...}\n\n`:

```json
{ "stage": "reading",    "message": "Reading transcript",         "detail": "175,827 characters" }
{ "stage": "splitting",  "message": "Splitting into 10 chunks",   "detail": "chunk_size=20000" }
{ "stage": "chunk",      "message": "Summarizing chunk 3 of 10",  "detail": "..." }
{ "stage": "merging",    "message": "Merging 10 chunk summaries", "detail": "..." }
{ "stage": "summary",    "message": "Extracting topics & concepts" }
{ "stage": "concept_map","message": "Drawing concept map" }
{ "stage": "questions",  "message": "Generating 8 quiz questions" }
{ "stage": "saving",     "message": "Saving session" }
{ "stage": "done",       "result": { ...full AnalyzeResult... } }
```

Keepalive comments (`: keepalive`) are sent every second while waiting for LLM responses.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `ModuleNotFoundError: structlog` | Wrong Python / uvicorn being used | Use `/usr/local/bin/python3 -m uvicorn` explicitly |
| `SSLCertVerificationError` on Whisper download | Python 3.10 (python.org) missing CA certs | Run `"/Applications/Python 3.10/Install Certificates.command"` |
| `n_keep >= n_ctx` context error | Model loaded with default 4096 context | Reload: `lms load <model> --context-length 32768 -y` |
| Timeout after 120 seconds | LM Studio/Ollama idle connection timeout | Already fixed — streaming mode is always used for local providers |
| "Session not found" after restart | Using `storage: memory` | Switch to `storage: sqlite` in `config.yaml` |
| MCQ shows correct answer pre-filled | React reusing component state | Already fixed — `key={question.id}` forces fresh mount |
| CORS error in browser | Frontend URL not in allowed origins | Add `http://localhost:5173` to `config.yaml → server → cors_origins` |
| Whisper slow on first use | Model downloading (~1.5 GB for medium) | One-time download — cached forever after; use `tiny` for demos |
| LM Studio picks MLX over GGUF | MLX variant present | Delete `~/.lmstudio/models/<model-name>-MLX-*/` so only GGUF remains |
| Frontend blank / 404 | Backend not running | Start backend first; check port 8000 |

---

## Running Tests

```bash
cd backend
pytest tests/ -v --tb=short

# Run a specific test file:
pytest tests/test_routers.py -v

# Run with coverage:
pytest tests/ --cov=. --cov-report=term-missing
```

---

## Supported Transcript Formats

Distill accepts any text input with instructor speech. No specific format required.

| Source | How to export |
|---|---|
| Microsoft Teams | Meeting recap → Download transcript (`.vtt`) |
| Zoom | Cloud recordings → Transcript (`.vtt`) |
| Google Meet | Meeting notes → Transcript (`.txt`) |
| Manual | Paste directly into the text area |
| Word doc | Upload `.docx` — text is extracted automatically |

Minimum 100 characters. There is no maximum — the map-reduce pipeline handles transcripts of any length.

---

## License

MIT — for educational use as part of the GenAI-2026 curriculum by Inceptez.
