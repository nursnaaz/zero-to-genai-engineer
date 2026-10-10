# Session 15 — LLM Fine-Tuning (PEFT · LoRA · QLoRA)

### When RAG is not enough: teach the model *how* to talk, without retraining every weight.

---

**MISSING from S14:** You can ship an agent on AWS. The model still speaks like a generic assistant. Fine-tuning (especially **LoRA / QLoRA**) changes style, format, and domain phrasing. **RAG** still owns fresh facts and citations — this session teaches when to use which, and how quantization makes training fit on a single GPU.

| File | What it is |
|---|---|
| [`teaching_decks/teach_01_finetuning_lora_qlora.html`](./teaching_decks/teach_01_finetuning_lora_qlora.html) | **Classroom deck** — RAG vs fine-tuning, PEFT → LoRA → quantization → QLoRA (worked math + Plays) |
| [`teaching_decks/README.md`](./teaching_decks/README.md) | How to open the deck |
| [`unsloth_finetuning.ipynb`](./unsloth_finetuning.ipynb) | Hands-on Unsloth fine-tuning notebook |

## Classroom

1. Open the HTML deck in Chrome (arrows / Page Down; hit **Play** where shown).
2. Run the Unsloth notebook (GPU recommended — Colab Pro or a local CUDA box).

## Decision in one line

| Need | Prefer |
|---|---|
| Fresh facts, policies, citations that change often | **RAG** |
| Tone, format, slang, domain *behavior* | **Fine-tune (LoRA / QLoRA)** |
| Both | **Hybrid** — retrieve facts, fine-tune how answers are phrased |

← [Course README](../README.md) · [S14 Bedrock AgentCore](../14_Bedrock_AgentCore/) · [S17 Decision Models](../17_Decision_Models/)
