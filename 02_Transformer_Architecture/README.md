# Session 02 — Transformer Architecture

> **The big question:** How does the same word mean different things in different sentences — and how does a model know the difference?

In Session 01, every embedding method gave each word one fixed vector. `"bank"` (river) and `"bank"` (finance) got the same representation. The Transformer solves this with **self-attention** — a mechanism that builds a new, context-aware vector for each word by looking at every other word in the sentence simultaneously.

This session builds an Encoder-Decoder Transformer from scratch in PyTorch, following the original *Attention is All You Need* paper. By the end, you will have trained a working English → Italian translation model.

---

## 📋 Assignments

> [!IMPORTANT]
> Two assignments to complete after this session. Share your work in the WhatsApp group.

| # | Type | Assignment | Due |
|---|------|-----------|-----|
| A1 | ✍️ Article | Deep Dive: Transformer Architecture | Next session |
| A2 | 💻 Run | Train the notebook end-to-end on Colab Pro | Next session |

---

### A1 — Medium Article: Transformer Architecture Deep Dive

Write a Medium article explaining **how the Transformer architecture works**, aimed at a complete beginner who just finished this session.

Your article must cover all of these components with at least one concrete example or analogy each:

- **The problem** — why RNNs and fixed embeddings weren't enough (context-dependence, vanishing gradients)
- **Self-Attention** — how Query, Key, and Value vectors work; what "scaled dot-product attention" computes; why it lets every word look at every other word
- **Multi-Head Attention** — why running attention 8 times in parallel captures richer relationships than once
- **Positional Encoding** — why we need it (Transformers have no built-in sense of order), how sine/cosine signals encode position
- **The Encoder** — what it does, how the 6 encoder blocks stack together
- **The Decoder** — how it differs from the encoder, what cross-attention is, why it needs to look at the encoder output
- **Residual connections and Layer Normalisation** — what they stabilise and why they matter
- **The full picture** — how all components combine to produce a translation from English to Italian

Aim for 1,500–2,500 words. Use diagrams or your own hand-drawn sketches if they help.

---

### A2 — Run the Notebook: Train a Transformer on Colab Pro

Open the notebook in Google Colab Pro and run it end-to-end. Train the English → Italian translation model, observe the results, and experiment with the predictions.

#### Why Colab Pro is required

Training a Transformer — even a small one — requires a high-powered GPU. The free Colab tier provides a T4 GPU which is **not sufficient** for this notebook; training will either time out or take many hours.

**You need Google Colab Pro** which gives access to A100 and H100 GPUs.

> **Google Colab Pro costs approximately $10/month** (billed in compute units).
> Sign up at: [colab.research.google.com](https://colab.research.google.com) → click **"Upgrade"**
> Select runtime: `Runtime → Change runtime type → H100 GPU`

With an H100, the full training run (6 epochs on `opus_books` English → Italian) completes in roughly 20–40 minutes.

#### What to do in the notebook

1. Open the notebook using the **"Open in Colab"** badge in the notebook file
2. Connect to an **H100 GPU** runtime (`Runtime → Change runtime type → H100 GPU`)
3. Run all cells from top to bottom — read each section as you go
4. Once training completes, run the test translation cells and observe the output
5. **Experiment:** change the `test_sentences` list at the bottom and try your own English sentences
6. Screenshot your translation results and share in the WhatsApp group

---

## What's MISSING after this session?

The Transformer solves context-dependence — but training one from scratch takes hours and significant compute.

In practice, nobody trains a Transformer from scratch. They take a **pre-trained model** (GPT, BERT, Gemini) and interact with it via an API — passing carefully crafted text called a **prompt** to control what it produces.

That gap — **how to use a pre-trained LLM efficiently** — is what the next sessions cover: tokenization, context windows, embeddings, and API calls.

---

## Notebooks

> ⚠️ **Requires Google Colab Pro (H100 GPU).** The building-blocks section (Part 1) runs on CPU, but the training loop (Part 2) will not complete without a high-powered GPU. See the A2 assignment above for setup instructions.

| # | Notebook | What You Build | Time |
|---|---|---|---|
| 01 | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/nursnaaz/zero-to-genai-engineer/blob/main/02_Transformer_Architecture/notebooks/01_transformer_from_scratch.ipynb) [transformer_from_scratch.ipynb](notebooks/01_transformer_from_scratch.ipynb) | Full Encoder-Decoder Transformer in PyTorch — embeddings, positional encoding, multi-head attention, encoder/decoder stacks, training loop on English → Italian | 90 min |

---

## Slides

| File | Contents |
|---|---|
| [Transformers.pptx.pdf](slides/Transformers.pptx.pdf) | Full Transformer architecture walkthrough — attention, encoder-decoder, positional encoding |

---

## Papers

| File | What It Is |
|---|---|
| [Attention_Is_All_You_Need.pdf](papers/Attention_Is_All_You_Need.pdf) | The original 2017 paper by Vaswani et al. — read alongside the notebook |

---

## Interactive Tutorials

Before or after running the notebook, go through these interactive tutorials. Each one walks you through the core concepts with step-by-step calculations — built specifically for this course.

| Tutorial | What It Covers | Level | Time |
|---|---|---|---|
| [Self-Attention Mechanism](https://nursnaaz.github.io/tutorial/self-attention) | How Query, Key, and Value work — step-by-step using "I bought apple to eat" | Beginner | 30 min |
| [Positional Encoding](https://nursnaaz.github.io/tutorial/positional-encoding) | Why self-attention is blind to word order, and how sinusoidal encoding solves it — with full calculations from the original paper | Beginner | 35 min |
| [Multi-Head Attention](https://nursnaaz.github.io/tutorial/multi-head-attention) | How 3 attention heads run in parallel — semantic, syntactic, and purpose-driven relationships computed step-by-step | Intermediate | 60 min |

These tutorials are interactive — you can run the calculations yourself in the browser. Use them to verify your understanding before writing the A1 article.

---

## Videos

These videos were created with care to help you build a visual intuition for self-attention before reading any code. **Watch them before opening the notebook.**

| File | What It Covers | How to Use |
|---|---|---|
| [SelfAttentionFull.mp4](assets/SelfAttentionFull.mp4) | Complete self-attention walkthrough — how tokens attend to each other, what Q/K/V mean visually | Watch first, before the notebook |
| [self_attention_animation.gif](assets/self_attention_animation.gif) | Animated attention weights across a sentence — see which words attend to which | Use as a quick reference while reading the theory |

---

## What the Notebook Covers

The notebook follows the architecture diagram from the paper step by step:

| Component | What You Build |
|---|---|
| `InputEmbeddings` | Token → dense vector (d_model = 512) |
| `PositionalEncoding` | Sine/cosine positional signal added to embeddings |
| `LayerNormalization` | Stabilises training — why epsilon matters |
| `ResidualConnection` | Skip connections to prevent vanishing gradients |
| `FeedForwardBlock` | Two-layer MLP after each attention block |
| `MultiHeadAttention` | Q / K / V projections, scaled dot-product, 8 heads |
| `EncoderBlock` + `EncoderStack` | 6 stacked encoder layers |
| `DecoderBlock` + `DecoderStack` | 6 stacked decoder layers with cross-attention |
| `LinearProjectionLayer` | Projects decoder output to vocabulary logits |
| `Transformer` + `build_transformer()` | Full assembled model |
| Training loop | English → Italian translation on `opus_books` dataset |

---

## Setup

```bash
# Install dependencies (or use Colab Pro — no local setup needed)
pip install torch transformers tokenizers datasets tqdm
```

For Colab: click the **"Open in Colab"** badge above, upgrade to **Colab Pro**, and select `Runtime → Change runtime type → H100 GPU`.
