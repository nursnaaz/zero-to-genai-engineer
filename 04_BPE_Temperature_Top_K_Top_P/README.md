# 04 — BPE Tokenization & Sampling Parameters
### M01 Foundation — Part 1 of 2 · Modern LLM Internals

> **Where we are in the curriculum:**
>
> | Session | Covers |
> |---|---|
> | S00 + S01 | Text → Numbers (TF-IDF, embeddings, search) |
> | S02 | Transformer Architecture (self-attention, encoder-decoder) |
> | S03 | GPT Evolution & Alignment (GPT-1/2/3 → ChatGPT → Claude) |
> | **S04 ← you are here** | **BPE Tokenization & Sampling Parameters (how LLMs read and generate text)** |
>
> S04 begins M01: Modern LLM Fundamentals. We go inside the pipeline.

---

> **What was MISSING from S03?**
>
> S03 showed us the full story of how GPT evolved — from a simple text predictor to an aligned assistant.  
> But we never looked inside the pipeline itself.  
>
> Two questions remained unanswered:
> 1. **How does an LLM turn words into numbers?** The model never sees raw text — it sees integer IDs. *How are those IDs decided?*
> 2. **How does an LLM decide which word to generate next?** It doesn't pick the most probable word every time. *What controls that choice?*
>
> This session answers both.

---

## What This Session Covers

```
Words → BPE tokens → token IDs   (the input side)
Logits → softmax → temperature/top-K/top-P → sampled token   (the output side)
```

| Topic | Key Idea |
|---|---|
| **Why character-level tokenization fails** | Too many steps; model can't learn word-level patterns |
| **Why word-level tokenization fails** | Vocabulary explodes; unseen words ("tokenizing") become `<UNK>` |
| **Byte Pair Encoding (BPE)** | Start with characters. Repeatedly merge the most frequent pair. Build a fixed vocab of subwords. |
| **Temperature** | Divide logits by T before softmax. Low T = confident/repetitive. High T = creative/random. |
| **Top-K sampling** | Only consider the K most probable next tokens. |
| **Top-P (nucleus) sampling** | Only consider the smallest set of tokens whose probabilities sum to at least P. |
| **Combining all three** | Temperature first → Top-K filter → Top-P filter → sample. Order matters. |

---

## Interactive Workbooks — Open These Alongside the Notebooks

The two Excel workbooks in this folder walk through the algorithms step by step with no code required. Open them first if you want to build intuition before running the notebooks.

| Workbook | What it shows |
|---|---|
| `bpe_step_by_step.xlsx` | BPE merge rounds on a tiny corpus — each sheet is one merge step. Watch the vocab grow. |
| `llm_temperature_topp_topk.xlsx` | A fixed probability distribution — see how temperature, top-K, and top-P each change the sampling pool. |

---

## Folder Structure

```
04_BPE_Temperature_Top_K_Top_P/
│
├── README.md                          ← you are here
│
├── bpe_step_by_step.xlsx              ← interactive BPE walkthrough — open before NB1
├── llm_temperature_topp_topk.xlsx     ← interactive sampling walkthrough — open before NB2
│
└── notebooks/
    ├── NB1_BPE_Tokenization.ipynb            ← BPE from scratch + tiktoken comparison
    └── NB2_Temperature_TopK_TopP.ipynb       ← sampling math + Gemini API experiments
```

---

## The Two Notebooks

| | NB1 — BPE Tokenization | NB2 — Temperature / Top-K / Top-P |
|---|---|---|
| **Colab link** | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/nursnaaz/zero-to-genai-engineer/blob/main/04_BPE_Temperature_Top_K_Top_P/notebooks/NB1_BPE_Tokenization.ipynb) | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/nursnaaz/zero-to-genai-engineer/blob/main/04_BPE_Temperature_Top_K_Top_P/notebooks/NB2_Temperature_TopK_TopP.ipynb) |
| **Topic** | How LLMs turn text into numbers | How LLMs decide which word comes next |
| **Section 1** | Why char/word tokenization fails; BPE algorithm from scratch | Logits → softmax → probability distribution |
| **Section 2** | Implement `build_bpe_vocab()` and `tokenize_with_bpe()` | Implement `apply_temperature()`, `top_k_filter()`, `top_p_filter()` |
| **Section 3** | Compare GPT-2 vs GPT-4 tokenization using `tiktoken` | Run Gemini API at different temperatures/top-K/top-P; observe coherence vs creativity |
| **Section 4** | Challenge: tokenize a code snippet; compare your BPE vs tiktoken | Challenge: build a full `sample_token()` combining all three in the correct order |
| **Install** | `!pip install tiktoken` | `!pip install google-generativeai matplotlib numpy` |
| **API key needed** | No | Yes — `GEMINI_API_KEY` |
| **Time** | ~45 min | ~45 min |

---

## Key Concepts

### Byte Pair Encoding (BPE)

BPE is the tokenization algorithm used by GPT-2, GPT-3, GPT-4, LLaMA, and most modern LLMs.

**The core idea in three sentences:**
1. Start with a vocabulary of individual characters.
2. Count all adjacent pairs of symbols in the training corpus.
3. Merge the most frequent pair into a new symbol. Repeat until the vocabulary reaches the target size.

**Why it works:** Common words ("the", "is") become single tokens. Rare or unknown words are split into meaningful subwords ("tokeniz" + "ation"). Numbers, code, and punctuation are handled gracefully.

**Why it matters for you:** Token count determines API cost. `tiktoken` is the official BPE library for OpenAI models. Knowing BPE helps you write prompts that cost less.

---

### Temperature

Temperature T scales the logits before softmax:

```
adjusted_logit[i] = logit[i] / T
probability[i]    = softmax(adjusted_logit)[i]
```

| Temperature | Effect |
|---|---|
| T < 1.0 | Sharpens the distribution — model picks the likely tokens more often |
| T = 1.0 | No change — raw softmax probabilities |
| T > 1.0 | Flattens the distribution — model becomes more exploratory |

**Rule of thumb:** Use T = 0.2–0.4 for factual/code tasks. Use T = 0.8–1.0 for creative writing.

---

### Top-K Sampling

After applying temperature, keep only the K tokens with the highest probability. Re-normalise and sample from those K tokens only.

- K = 1 → greedy decoding (always the most probable token)
- K = 50 → a common default
- K = vocab size → no filtering (pure sampling)

---

### Top-P (Nucleus) Sampling

Sort tokens by probability (highest first). Keep adding tokens to the "nucleus" until their cumulative probability reaches P. Sample from the nucleus only.

- P = 0.9 → sample from the smallest set of tokens that together account for 90% of probability mass
- P = 1.0 → no filtering
- P = 0.1 → very conservative — nucleus is tiny, near-greedy

**Top-P adapts to the distribution.** When the model is confident (one token dominates), the nucleus is tiny. When the model is uncertain (many tokens are plausible), the nucleus expands automatically. This makes top-P more robust than top-K in practice.

---

### Correct Order: Temperature → Top-K → Top-P

This is a common source of bugs in LLM implementations:

```
1. Apply temperature   (rescale logits)
2. Apply top-K filter  (zero out everything outside top K)
3. Apply top-P filter  (further narrow to nucleus)
4. Sample              (pick one token)
```

Top-K and top-P are applied to the already-temperature-adjusted distribution.

---

## Prerequisites

- S02: Transformer Architecture (you should understand what logits are — the raw output of the final linear layer)
- S03: GPT Evolution (you should know that GPT generates one token at a time)
- Basic Python (lists, dicts, sorting, list comprehensions)

---

## Time Estimate

| Activity | Time |
|---|---|
| Open `bpe_step_by_step.xlsx` and follow the merge steps | 15 min |
| Open `llm_temperature_topp_topk.xlsx` and adjust sliders | 15 min |
| NB1 — BPE Tokenization (all 4 sections) | 45 min |
| NB2 — Temperature / Top-K / Top-P (all 4 sections) | 45 min |
| Assignments below | 2–3 hrs |

---

## Assignments

Complete these before the next session.

---

### Assignment 1 — BPE Workbook + NB1 (45 min)

**Step 1 — Workbook**
- [ ] Open `bpe_step_by_step.xlsx`
- [ ] Follow the merge steps sheet by sheet
- [ ] Answer in a comment: after how many merges does the token `"ing"` appear in the vocabulary?

**Step 2 — NB1**
- [ ] Run NB1 all the way through
- [ ] Complete the Section 2 TODOs: implement `build_bpe_vocab()` and `tokenize_with_bpe()`
- [ ] In Section 3: tokenize `"ChatGPT is an artificial intelligence chatbot"` with `gpt2`, `gpt-4`, and `cl100k_base` encodings. Write down the token counts for each.

**Step 3 — Explore**
- [ ] Tokenize the same sentence in English, Hindi (romanised), and a sentence with lots of numbers (e.g. `"The year 2024 had 366 days and 8784 hours"`)
- [ ] Answer: which type of text is most "expensive" in tokens per word, and why?

---

### Assignment 2 — Sampling Workbook + NB2 (45 min)

**Step 1 — Workbook**
- [ ] Open `llm_temperature_topp_topk.xlsx`
- [ ] Adjust the temperature slider from 0.1 to 2.0 and observe the probability distribution change
- [ ] Answer: at what temperature does the second-ranked token's probability roughly equal the first-ranked token's probability?

**Step 2 — NB2**
- [ ] Run NB2 all the way through
- [ ] Complete the Section 2 TODOs: implement `apply_temperature()`, `top_k_filter()`, `top_p_filter()`
- [ ] Run the Section 3 Gemini experiments at `temperature=0.1`, `0.7`, and `1.2`
- [ ] Copy one interesting output at each temperature into a comment

**Step 3 — Section 4 Challenge**
- [ ] Implement `sample_token()` that chains temperature → top-K → top-P → sample
- [ ] Run it 10 times on the same logits and observe the variance

---

### Assignment 3 — Reflection (10 min)

Post in the WhatsApp group with:
1. A screenshot of your NB1 tiktoken comparison table (the token counts for different encodings)
2. A screenshot of your NB2 matplotlib visualisation (the probability distribution at three temperatures)
3. One sentence answering: *"Before this session, how did you think LLMs chose their next word? What changed?"*

---

*Part of the GenAI-2026 curriculum — zero-to-genai-engineer track*
