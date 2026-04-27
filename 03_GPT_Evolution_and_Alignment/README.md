# 03 — GPT Evolution and Alignment
### 🏁 M00 Foundation — Part 3 of 3 · Completes M00

> **M00 is now complete.** This is the final piece of the Foundation module:
>
> | Session | Covers |
> |---|---|
> | S00 + S01 | Text → Numbers (TF-IDF, embeddings, search) |
> | S02 | Transformer Architecture (self-attention, encoder-decoder) |
> | **S03 ← you are here** | **GPT Evolution & Alignment (GPT-1/2/3 → ChatGPT → Claude)** |
>
> Together, S00–S03 take you from raw text to understanding how modern LLMs are built and aligned.

---

> **Where we are:** We built a Transformer from scratch in S02. Now we follow the full story of how that architecture became GPT-1, GPT-2, GPT-3, and ultimately the aligned assistants (ChatGPT, Claude) we use today — including the research papers that made each step possible.

---

## 🗺️ What This Module Covers

```
Text Prediction (GPT-1) → Scale (GPT-2 → GPT-3) → Alignment (RLHF → CAI → DPO)
```

| Track | Papers Covered |
|---|---|
| **GPT Series** | GPT-1, GPT-2, GPT-3 |
| **Encoder Models** | BERT, BART (contrast with GPT's decoder-only approach) |
| **Alignment** | InstructGPT, HH-RLHF, Constitutional AI, RLAIF, DPO, SELF-REFINE |

---

## 📁 Folder Structure

```
03_GPT_Evolution_and_Alignment/
│
├── README.md                          ← you are here
│
├── notebooks/                         ← hands-on code
│   ├── NB1_GPT_PyTorch_Detailed_Shakespeare.ipynb   ← deep dive, real Shakespeare
│   └── NB2_GPT_TensorFlow_Minimal_Synthetic.ipynb   ← quick overview, synthetic data
│
├── papers/                            ← original research papers
│   ├── 01_gpt_series/
│   │   ├── GPT1_Language_Understanding_2018.pdf
│   │   ├── GPT2_Unsupervised_Multitask_Learners_2019.pdf
│   │   └── GPT3_Few_Shot_Learners_2020.pdf
│   ├── 02_encoder_models/
│   │   ├── BERT_Bidirectional_Transformers_2018.pdf
│   │   └── BART_Denoising_Seq2Seq_2019.pdf
│   └── 03_alignment/
│       ├── InstructGPT_RLHF_2022.pdf
│       ├── Helpful_Harmless_Assistant_RLHF_2022.pdf
│       ├── Constitutional_AI_Harmlessness_2022.pdf
│       ├── RLAIF_Scaling_RLHF_2023.pdf
│       ├── DPO_Direct_Preference_Optimization_2023.pdf
│       └── SELF_REFINE_Iterative_Refinement_2023.pdf
│
├── paper_summaries/                   ← beginner-friendly summary notebooks
│   ├── 01_GPT1_Language_Understanding.ipynb
│   ├── 02_GPT2_Unsupervised_Multitask_Learners.ipynb
│   ├── 03_GPT3_Few_Shot_Learners.ipynb
│   ├── 04_BERT_Bidirectional_Transformers.ipynb
│   ├── 05_BART_Denoising_Seq2Seq.ipynb
│   ├── 06_InstructGPT_RLHF.ipynb
│   ├── 07_Helpful_Harmless_Assistant_RLHF.ipynb
│   ├── 08_Constitutional_AI_Harmlessness.ipynb
│   ├── 09_RLAIF_Scaling_RLHF.ipynb
│   ├── 10_DPO_Direct_Preference_Optimization.ipynb
│   └── 11_SELF_REFINE_Iterative_Refinement.ipynb
│
└── assets/                            ← generated outputs from notebook runs
    ├── training_loss.png
    ├── finetuning_progress.png
    ├── next_token_probs.png
    ├── attn_L1_H1.png
    └── gpt_shakespeare.pt             ← trained model checkpoint
```

---

## 📓 The Two Notebooks

Start with NB2 to get the big picture, then do NB1 to understand every detail.

| | NB1 — PyTorch Deep Dive | NB2 — TensorFlow Overview |
|---|---|---|
| **File** | `NB1_GPT_PyTorch_Detailed_Shakespeare.ipynb` | `NB2_GPT_TensorFlow_Minimal_Synthetic.ipynb` |
| **Depth** | Detailed — every layer hand-coded | Minimal — Keras handles internals |
| **Dataset** | Real Shakespeare (1.1 M chars) | Synthetic sentences (Space/Ocean/Medieval) |
| **Tokenizer** | Char / Word / BPE — your choice | Character-level only |
| **Training** | Manual loop: AdamW + cosine LR + grad clip | `model.fit()` — 1 line |
| **Generation** | Token-by-token with live top-5 display | Single generate call |
| **Time** | ~2–3 hours | ~30 min |
| **Best for** | Understanding HOW GPT works | Seeing WHAT the pipeline looks like |

---

## 📄 Papers — Reading Guide

### 🔢 Recommended Reading Order

**Week 1 — The GPT Story (start here)**

| # | Paper | Summary Notebook | Key Question |
|---|---|---|---|
| 1 | GPT-1 (2018) | `paper_summaries/01_GPT1_Language_Understanding.ipynb` | Can pre-training on unlabelled text help downstream tasks? |
| 2 | GPT-2 (2019) | `paper_summaries/02_GPT2_Unsupervised_Multitask_Learners.ipynb` | What if we scale and remove fine-tuning entirely? |
| 3 | GPT-3 (2020) | `paper_summaries/03_GPT3_Few_Shot_Learners.ipynb` | What happens at 175B params? |

**Week 2 — Contrast: Encoder vs Decoder**

| # | Paper | Summary Notebook | Key Question |
|---|---|---|---|
| 4 | BERT (2018) | `paper_summaries/04_BERT_Bidirectional_Transformers.ipynb` | What if we read text in both directions? |
| 5 | BART (2019) | `paper_summaries/05_BART_Denoising_Seq2Seq.ipynb` | What if we combine BERT + GPT in one model? |

**Week 3 — Alignment: Making GPT Safe and Helpful**

| # | Paper | Summary Notebook | Key Question |
|---|---|---|---|
| 6 | InstructGPT (2022) | `paper_summaries/06_InstructGPT_RLHF.ipynb` | How do we make GPT-3 follow instructions? → ChatGPT |
| 7 | HH-RLHF (2022) | `paper_summaries/07_Helpful_Harmless_Assistant_RLHF.ipynb` | How do we train helpful AND harmless? → Claude |
| 8 | Constitutional AI (2022) | `paper_summaries/08_Constitutional_AI_Harmlessness.ipynb` | Can AI replace human feedback for safety? |
| 9 | RLAIF (2023) | `paper_summaries/09_RLAIF_Scaling_RLHF.ipynb` | Google's validation: AI feedback ≈ human feedback |
| 10 | DPO (2023) | `paper_summaries/10_DPO_Direct_Preference_Optimization.ipynb` | Can we skip the reward model entirely? |
| 11 | SELF-REFINE (2023) | `paper_summaries/11_SELF_REFINE_Iterative_Refinement.ipynb` | Can a model improve its own outputs? |

---

## 🧠 The Big Picture — GPT Evolution Timeline

```
2017  Attention Is All You Need          → The Transformer architecture
      │
2018  GPT-1  (OpenAI)                   → Pre-train + fine-tune
      BERT   (Google)                   → Bidirectional, encoder-only
      │
2019  GPT-2  (OpenAI)                   → Zero-shot, scale to 1.5B
      BART   (Facebook)                 → Encoder + Decoder, denoising
      │
2020  GPT-3  (OpenAI)                   → Few-shot, scale to 175B
      │
2022  InstructGPT  (OpenAI)             → RLHF → ChatGPT
      HH-RLHF      (Anthropic)          → Helpful + Harmless → Claude
      Constitutional AI (Anthropic)    → AI feedback replaces human labels
      │
2023  RLAIF   (Google)                  → Validates AI feedback at scale
      DPO     (Stanford)                → No reward model, no PPO
      SELF-REFINE (CMU/AI2)             → Self-improvement without training
      │
2024+ GPT-4, Claude 3, Gemini…          → What you use today
```

---

## 🎯 Key Concepts by Topic

### Why Decoder-Only Won
BERT and BART showed that bidirectional models are better at understanding.  
But GPT won the LLM race because **generation > classification** in the ChatGPT era.  
Today: GPT-4, Claude, Gemini, LLaMA are all decoder-only.

### The Alignment Problem in One Sentence
A model trained to predict text is not the same as a model trained to be helpful.  
RLHF (InstructGPT), CAI (Anthropic), and DPO (Stanford) are three answers to the same question: *how do you get from a text predictor to a useful assistant?*

### DPO vs RLHF — Why It Matters for Engineers
If you want to fine-tune an open-source model (LLaMA, Mistral) with preference data, use **DPO** — it's simpler, stabler, and achieves the same results without PPO expertise.

---

## ✅ Prerequisites
- Module 02: Transformer Architecture (you should know self-attention, encoder vs decoder)
- Basic Python + PyTorch or TensorFlow familiarity

## ⏱️ Time Estimate
| Activity | Time |
|---|---|
| NB2 (TF overview) | 30 min |
| NB1 (PyTorch deep dive) | 2–3 hours |
| Paper summaries (all 11) | 4–5 hours |
| Original papers (selective) | 6–8 hours |

---

*Part of the GenAI-2026 curriculum — zero-to-genai-engineer track*
