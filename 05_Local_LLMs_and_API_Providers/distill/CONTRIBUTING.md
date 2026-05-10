# Contributing to Distill

Welcome! Distill is a real production project built as part of the
**[Zero to GenAI Engineer](https://github.com/nursnaaz/zero-to-genai-engineer)** course.
Contributing here is part of your learning — you will write real code, go through a real
code review, and your change will ship to real users.

Mohamed reviews every PR personally. Good contributions get merged. All contributions
get feedback.

---

## What Can I Contribute?

| Type | Examples |
|---|---|
| **Bug fix** | Something crashes or gives wrong output |
| **New LLM provider** | Add support for Cohere, Mistral, Together AI |
| **New STT provider** | Add AssemblyAI, Deepgram |
| **Prompt improvement** | Better summary, quiz, or evaluation prompts |
| **UI improvement** | Better layout, new feature on a page |
| **Documentation** | Fix a typo, improve the README, add an example |
| **Tests** | Add test coverage for an untested function |

Not sure? Open an
[Issue](https://github.com/nursnaaz/distill/issues/new) first and describe what
you want to do. Mohamed will reply and tell you whether it's a good fit.

---

## Step-by-Step: Your First Pull Request

### Step 1 — Fork the repository

A **fork** is your own copy of Distill on GitHub. You make changes in your fork, then
propose them back to the original via a Pull Request.

1. Go to **[github.com/nursnaaz/distill](https://github.com/nursnaaz/distill)**
2. Click the **Fork** button in the top-right corner
3. GitHub creates `github.com/YOUR_USERNAME/distill` — this is yours to experiment with

---

### Step 2 — Clone your fork to your machine

```bash
# Replace YOUR_USERNAME with your actual GitHub username
git clone https://github.com/YOUR_USERNAME/distill.git
cd distill
```

---

### Step 3 — Add the original repo as "upstream"

This lets you pull in Mohamed's latest changes later without losing your own work.

```bash
git remote add upstream https://github.com/nursnaaz/distill.git

# Verify you have two remotes:
git remote -v
# origin   https://github.com/YOUR_USERNAME/distill.git  (your fork)
# upstream https://github.com/nursnaaz/distill.git       (the original)
```

---

### Step 4 — Create a branch for your change

**Never work directly on `main`.** Create a branch with a short, descriptive name.

```bash
# Pull the latest code first
git checkout main
git pull upstream main

# Create your branch
git checkout -b your-branch-name
```

Good branch names:

| What you're doing | Branch name |
|---|---|
| Fix a crash in the evaluator | `fix/evaluator-json-crash` |
| Add Cohere provider | `feat/cohere-provider` |
| Improve the summary prompt | `improve/summary-prompt` |
| Fix a README typo | `docs/fix-readme-typo` |

---

### Step 5 — Set up the project locally

**Backend (Python):**
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend (React):**
```bash
cd frontend
npm install
npm run dev
```

**LLM server** — you need one of:
- **LM Studio** (recommended): download [lmstudio.ai](https://lmstudio.ai), load `qwen/qwen3-4b-2507` with `--context-length 32768`
- **Ollama**: `ollama pull qwen2.5:7b`

See the full setup guide in [README.md](./README.md).

---

### Step 6 — Make your change

Edit the code. Some pointers:

- **Backend changes** — backend auto-reloads on save (`--reload` flag)
- **Frontend changes** — Vite hot-reloads instantly
- **Prompt changes** — edit `.j2` files in `prompts/`, no restart needed
- **Config changes** — edit `config.yaml`, restart backend

Run the linter before committing:
```bash
# Backend
cd backend && ruff check . && black --check .

# Frontend
cd frontend && npm run lint
```

---

### Step 7 — Commit your change

Write a clear commit message that explains **what** changed and **why**.

```bash
git add <the files you changed>
git commit -m "fix: evaluator falls back gracefully when LLM returns empty JSON"
```

Commit message format:

| Prefix | When to use |
|---|---|
| `feat:` | New feature or provider |
| `fix:` | Bug fix |
| `improve:` | Enhancement to existing behaviour |
| `docs:` | Documentation only |
| `test:` | Tests only |
| `refactor:` | Code restructure, no behaviour change |

---

### Step 8 — Push to your fork

```bash
git push origin your-branch-name
```

---

### Step 9 — Open a Pull Request

1. Go to `github.com/YOUR_USERNAME/distill`
2. GitHub shows a yellow banner: **"Compare & pull request"** — click it
3. Fill in the PR form:

**Title** — one clear sentence:
```
fix: evaluator falls back gracefully when LLM returns empty JSON
```

**Description** — answer these three questions:
```
## What does this PR do?
Brief description of the change.

## Why is this needed?
What problem does it solve? Include the error message if it's a bug fix.

## How did you test it?
Describe what you ran to verify the fix works.
```

4. Click **Create Pull Request**

---

### Step 10 — Respond to review feedback

Mohamed will review your PR and leave comments. You might be asked to:

- Explain a design choice
- Fix a bug in your fix
- Add a test
- Rename a variable

**To update your PR**, simply push more commits to the same branch:
```bash
# Make the requested change
git add .
git commit -m "address review: rename variable to match convention"
git push origin your-branch-name
```

The PR updates automatically — no need to close and reopen it.

---

### Step 11 — Merge

Once Mohamed approves the PR, he will merge it. Your change is now live in the main
Distill codebase. 🎉

---

## Keeping Your Fork Up to Date

After Mohamed merges other PRs, your fork's `main` will be behind. Sync it like this:

```bash
git checkout main
git pull upstream main
git push origin main
```

Always do this before starting a new branch.

---

## Coding Standards

| Area | Standard |
|---|---|
| Python style | `ruff` + `black` (line length 100) |
| TypeScript style | `eslint` + `prettier` |
| Python files | Always start with `from __future__ import annotations` |
| Services | Depend only on `BaseLLMProvider`, never on concrete providers |
| Secrets | All in `.env`, never hardcoded |
| Config | All settings in `config.yaml`, never hardcoded |
| Tests | Add a test for every bug fix |

Run everything at once:
```bash
make lint
make test
```

---

## How to Add a New LLM Provider (Example)

Say you want to add **Cohere**:

**1.** Create `backend/providers/llm/cohere_provider.py`:
```python
from __future__ import annotations
from .base import BaseLLMProvider, LLMMessage, LLMResponse
from core.config import AppConfig

class CohereProvider(BaseLLMProvider):
    def __init__(self, config: AppConfig):
        import cohere
        self._client = cohere.AsyncClient(api_key=config.llm.api_key)
        self._model = config.llm.model

    async def complete(self, messages, temperature=None, max_tokens=None, response_format=None) -> LLMResponse:
        # Convert LLMMessage list → Cohere format, call API, return LLMResponse
        ...

    def get_provider_name(self) -> str: return "cohere"
    def get_model_name(self)    -> str: return self._model
```

**2.** Add one `elif` in `backend/providers/llm/factory.py`:
```python
elif provider == "cohere":
    from .cohere_provider import CohereProvider
    return CohereProvider(config)
```

**3.** Add config in `config.yaml`:
```yaml
llm:
  cohere:
    base_url: "https://api.cohere.ai/v1"
```

**4.** Add to `.env.example`:
```
COHERE_API_KEY=
```

**5.** Update `_resolve_api_key()` in `core/config.py` to check `COHERE_API_KEY`.

Switch providers with one line: `llm: provider: "cohere"` in `config.yaml`.

---

## Questions?

- Open a [GitHub Issue](https://github.com/nursnaaz/distill/issues/new) for bugs or feature ideas
- Ask Mohamed in the WhatsApp group for course-related questions
- Tag `@nursnaaz` in your PR description if you need a faster review

---

*Distill is part of the [Zero to GenAI Engineer](https://github.com/nursnaaz/zero-to-genai-engineer) curriculum by Mohamed Noordeen Alaudeen.*
