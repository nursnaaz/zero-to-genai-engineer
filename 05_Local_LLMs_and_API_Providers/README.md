# 05 — Running LLMs Locally and Via API Providers
### M01 Foundation — Part 2 of 2 · Completes M01

> **Where we are in M01:**
>
> | Session | Covers |
> |---|---|
> | S04 | BPE Tokenization + Sampling Parameters (temperature, top-K, top-P) |
> | **S05 ← you are here** | **Running LLMs locally (Ollama, LM Studio) and via cloud providers (OpenRouter, Databricks)** |
>
> S04 showed us what happens inside an LLM. S05 answers: how do we actually USE one?  
> API keys cost money, require internet, and lock you into one provider. This session teaches you to run LLMs locally for free AND switch between providers with one line of code.

---

> **MISSING chain:** S04 taught us how tokens flow through a model and how sampling parameters control output. But we were treating the LLM as a black box we call via one provider's API. What if that provider goes down? What if the cost is too high? What if you need to keep data on-premises? This session closes that gap: you will run a full LLM on your own machine and learn to call any cloud provider with a single unified pattern.

---

## What This Session Covers

| Topic | Tool | Why It Matters |
|---|---|---|
| **Local LLMs** | Ollama | Run Llama 3, Mistral, Phi-3 on your laptop — free, private, no internet needed |
| **Local LLMs (GUI)** | LM Studio | Point-and-click model download + OpenAI-compatible local server |
| **Multi-provider API** | OpenRouter | One API key, 100+ models — switch GPT-4o to Claude 3.5 by changing one string |
| **Enterprise LLMs** | Databricks | Call LLMs deployed inside a corporate data platform via REST endpoint |
| **Map-Reduce pattern** | LangChain + any provider | Summarise documents longer than the context window by splitting and merging |

---

## Folder Structure

```
05_Local_LLMs_and_API_Providers/
├── README.md                              ← you are here
├── slides.pdf                             ← session slides
├── notebooks/
│   ├── NB1_multi_provider_api_calls.ipynb   ← call 6 LLM providers with one unified pattern
│   ├── NB2_map_reduce_summarizer.ipynb      ← summarize long documents with map-reduce
│   ├── NB3_Ollama_Local_Setup.ipynb         ← run LLMs locally with Ollama
│   ├── NB4_OpenRouter_Multi_Provider.ipynb  ← access 100+ models via one API
│   ├── NB5_LMStudio_Local_Setup.ipynb       ← run LLMs locally with LM Studio
│   └── NB6_Databricks_Endpoint.ipynb        ← call enterprise LLMs via Databricks
├── apps/
│   ├── multi_provider_race.py               ← race 3 providers on the same prompt
│   └── map_reduce_demo.py                   ← full map-reduce pipeline demo
└── distill/                                 ← bonus project: Distill classroom assessment tool
```

---

## The Six Notebooks

| # | Notebook | What It Does | Run Where | Time |
|---|---|---|---|---|
| NB1 | `NB1_multi_provider_api_calls.ipynb` | Call OpenAI, Gemini, Anthropic, Ollama, OpenRouter, and Databricks with one unified `chat()` function — change provider by changing one variable | Colab or local | 30 min |
| NB2 | `NB2_map_reduce_summarizer.ipynb` | Summarise a 50-page document that exceeds the context window by splitting into chunks (map), summarising each (map), then merging the summaries (reduce) | Colab or local | 45 min |
| NB3 | `NB3_Ollama_Local_Setup.ipynb` | Install Ollama, pull Llama 3.2 or Phi-3, make your first local API call, stream output, compare models | **Local only** ⚠️ | 45 min |
| NB4 | `NB4_OpenRouter_Multi_Provider.ipynb` | Use one OpenRouter API key to call GPT-4o, Claude 3.5 Sonnet, Gemini 1.5 Pro, and Mistral — compare costs and responses side by side | Colab or local | 20 min |
| NB5 | `NB5_LMStudio_Local_Setup.ipynb` | Download a model in LM Studio's GUI, start the local server, call it from Python via the OpenAI-compatible endpoint | **Local only** ⚠️ | 30 min |
| NB6 | `NB6_Databricks_Endpoint.ipynb` | Call an LLM deployed on Databricks Model Serving via REST — the pattern used in enterprise environments | Colab or local | 15 min |

### Open in Colab

> NB3 and NB5 require a running local server — they **cannot** run in Google Colab.  
> Start with NB1 to get the big picture, then do NB3 or NB5 on your laptop.

| Notebook | Colab Link |
|---|---|
| NB1 — Multi-Provider API Calls | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/nursnaaz/zero-to-genai-engineer/blob/main/05_Local_LLMs_and_API_Providers/notebooks/NB1_multi_provider_api_calls.ipynb) |
| NB2 — Map-Reduce Summarizer | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/nursnaaz/zero-to-genai-engineer/blob/main/05_Local_LLMs_and_API_Providers/notebooks/NB2_map_reduce_summarizer.ipynb) |
| NB3 — Ollama Local Setup | ⚠️ Local only — see setup below |
| NB4 — OpenRouter Multi-Provider | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/nursnaaz/zero-to-genai-engineer/blob/main/05_Local_LLMs_and_API_Providers/notebooks/NB4_OpenRouter_Multi_Provider.ipynb) |
| NB5 — LM Studio Local Setup | ⚠️ Local only — see setup below |
| NB6 — Databricks Endpoint | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/nursnaaz/zero-to-genai-engineer/blob/main/05_Local_LLMs_and_API_Providers/notebooks/NB6_Databricks_Endpoint.ipynb) |

---

## Local Setup (NB3 — Ollama)

Ollama runs a local LLM server. Complete these steps before opening NB3:

```bash
# 1. Install Ollama (Mac / Linux)
curl -fsSL https://ollama.com/install.sh | sh

# 2. Pull a model (choose based on your RAM)
ollama pull phi3          # 2.7B — works on 8GB RAM
ollama pull llama3.2      # 3B  — works on 8GB RAM
ollama pull mistral       # 7B  — needs 16GB RAM

# 3. Confirm the server is running
curl http://localhost:11434/api/tags
```

> **Windows:** Download the installer from [ollama.com](https://ollama.com) — no terminal needed.

---

## Local Setup (NB5 — LM Studio)

LM Studio gives you a GUI to download and run any GGUF model:

1. Download LM Studio from [lmstudio.ai](https://lmstudio.ai)
2. Search for `Phi-3 Mini` or `Llama 3.2 3B` in the Discover tab and download it
3. Go to the **Local Server** tab and click **Start Server**
4. The server runs at `http://localhost:1234/v1` — same OpenAI-compatible format as Ollama
5. Open NB5 and run all cells

---

## Key Concepts

### Local vs Cloud LLMs

| | Local (Ollama / LM Studio) | Cloud (OpenAI / Gemini / OpenRouter) |
|---|---|---|
| **Cost** | Free forever | Pay per token |
| **Privacy** | Data never leaves your machine | Data sent to provider |
| **Speed** | Depends on your hardware | Consistent, fast |
| **Model size** | Limited by your RAM | Unlimited |
| **Internet** | Not needed | Required |
| **Best for** | Development, sensitive data, learning | Production, large models, teams |

### The Universal Chat Format

Every provider — whether it's OpenAI, Gemini, Ollama, or Databricks — accepts the same message structure:

```python
messages = [
    {"role": "system",    "content": "You are a helpful assistant."},
    {"role": "user",      "content": "Explain transformers in one sentence."},
    {"role": "assistant", "content": "..."},   # previous turns go here
    {"role": "user",      "content": "Next question..."},
]
```

Once you understand this format, switching providers is one variable change. That is what NB1 teaches.

### OpenRouter — The Model Marketplace

OpenRouter is a single API that proxies 100+ models from every major provider. Instead of managing 5 different API keys and 5 different SDKs, you use one key and change the `model=` string:

```python
# Same code. Different model string. Different provider.
model = "openai/gpt-4o"
model = "anthropic/claude-3-5-sonnet"
model = "google/gemini-1.5-pro"
model = "mistralai/mistral-7b-instruct"
model = "meta-llama/llama-3-70b-instruct"
```

Pricing is transparent — you see cost-per-token for every model before you call it.

### Map-Reduce for Long Documents

Context windows have limits. A 50-page PDF will not fit in a single prompt. Map-reduce is the solution:

```
Full document (50 pages)
       │
   ┌───┴───────────────────────────┐
   │    SPLIT into chunks           │  ← each chunk fits in context
   └───┬───────────────────────────┘
       │
   ┌───┴──────────────────────────────────────────────┐
   │  MAP — summarise each chunk independently         │  ← parallel LLM calls
   └───┬──────────────────────────────────────────────┘
       │
   ┌───┴────────────────────────────────────┐
   │  REDUCE — combine chunk summaries      │  ← one final LLM call
   └───┬────────────────────────────────────┘
       │
   Final summary
```

This is the same pattern used in production document intelligence pipelines (M11).

### Databricks for Enterprise

Databricks Model Serving lets companies deploy open-source models (Llama, Mistral) on their own cloud infrastructure and expose them as REST endpoints. The API format is identical to OpenAI's — the only difference is the `base_url` pointing to the company's Databricks workspace. NB6 covers this pattern so you can work in enterprise environments where data cannot leave the company's cloud.

---

## Prerequisites

- **S04** — You should understand BPE tokenization, context windows, and what temperature/top-K/top-P do
- Basic Python (functions, loops, dictionaries)
- A Gemini or OpenAI API key for NB1, NB2, NB4, NB6 (free tiers are fine)
- Your own laptop for NB3 (Ollama) and NB5 (LM Studio)

---

## Time Estimate

| Activity | Time | Notes |
|---|---|---|
| NB1 — Multi-provider calls | 30 min | Start here — works in Colab |
| NB2 — Map-reduce summarizer | 45 min | Works in Colab |
| NB3 — Ollama local setup | 45 min | Local only — requires install |
| NB4 — OpenRouter | 20 min | Works in Colab |
| NB5 — LM Studio local setup | 30 min | Local only — requires install |
| NB6 — Databricks endpoint | 15 min | Works in Colab |
| **Total (cloud notebooks only)** | **~1.5 hours** | NB1 + NB2 + NB4 + NB6 |
| **Total (including local)** | **~3 hours** | All six notebooks |

---

## This Week's Assignments

Complete these before the next session. Aim to finish the required assignments within 2–3 hours spread across the week.

---

### Assignment 1 — NB1: One Pattern, Six Providers (Required · 30 min)

Open `notebooks/NB1_multi_provider_api_calls.ipynb` and run every cell top to bottom.

- [ ] Run all cells and confirm you get a response from at least two providers
- [ ] Change the `PROVIDER` variable from `"gemini"` to `"openrouter"` — does the same code work?
- [ ] Find the cell where the unified `chat()` function is defined. Read it carefully — what does it abstract away?
- [ ] **Play around:** Pick any question and call it through three different providers. Copy the three responses into a notebook comment. Do they give the same answer? Are the styles different?
- [ ] **Question to answer:** In one sentence, what is the only thing you need to change to switch from Gemini to GPT-4o?

---

### Assignment 2 — NB2: Map-Reduce Summarizer (Required · 45 min)

Open `notebooks/NB2_map_reduce_summarizer.ipynb`.

**Step 1 — Run with the provided document**
- [ ] Run all cells with the default sample document
- [ ] Read each chunk's summary (the MAP output) — does it capture the key point of that section?
- [ ] Read the final merged summary (the REDUCE output) — does it feel coherent?

**Step 2 — Try your own document**
- [ ] Paste in any long article, blog post, or document you have
- [ ] Run the pipeline and read the output
- [ ] **Question to answer:** At what chunk size does the summary start to lose important details?

**Step 3 — Experiment with chunk size**
- [ ] Change the chunk size from the default to half its value. What happens to the number of LLM calls?
- [ ] Change it to double its value. What happens to the quality of each chunk summary?
- [ ] Write a one-sentence rule of thumb for choosing chunk size in a comment.

---

### Assignment 3 — NB3 or NB5: Run a Local LLM (Required · 45 min)

Choose either Ollama (NB3) or LM Studio (NB5). You only need to complete one.

**Option A — Ollama (NB3)**
- [ ] Install Ollama and pull `phi3` or `llama3.2`
- [ ] Run all cells in `NB3_Ollama_Local_Setup.ipynb`
- [ ] Confirm you get a streamed response in the streaming cell
- [ ] **Screenshot:** Take a screenshot of your terminal showing `ollama list` with your downloaded models. Post it in the WhatsApp group.

**Option B — LM Studio (NB5)**
- [ ] Install LM Studio, download a model, and start the local server
- [ ] Run all cells in `NB5_LMStudio_Local_Setup.ipynb`
- [ ] Confirm you get a response from the local server
- [ ] **Screenshot:** Take a screenshot of LM Studio's Local Server tab showing the server running. Post it in the WhatsApp group.

> If your laptop does not have enough RAM for any model (minimum 8GB free), skip this assignment and do Assignment 4 (NB4) twice — once with a cheap model and once with an expensive one.

---

### Assignment 4 — NB4: OpenRouter Model Race (Stretch · 20 min)

Open `notebooks/NB4_OpenRouter_Multi_Provider.ipynb`.

- [ ] Sign up for a free OpenRouter account at [openrouter.ai](https://openrouter.ai) and get an API key (free credits are provided)
- [ ] Run all cells — you will call 4 different models with the same prompt
- [ ] Look at the cost-per-token table OpenRouter returns — which model is the cheapest? Which is the most expensive?
- [ ] **Play around:** Change the test prompt to something domain-specific (e.g. a coding question, a legal question, a maths problem). Does a cheaper model do as well as a more expensive one for your domain?
- [ ] **Question to answer:** For everyday development tasks, does the cheapest model give acceptable results?

---

### Submission

Post in the WhatsApp group with:
1. A screenshot of NB1 showing a response from at least one provider
2. Your NB2 final merged summary — copy-paste the output text (a few sentences is fine)
3. A screenshot of your local LLM running (NB3 terminal output OR NB5 LM Studio server tab)
4. One sentence answering: *"When would you choose a local LLM over a cloud API?"*

---

*Part of the GenAI-2026 curriculum — zero-to-genai-engineer track*
