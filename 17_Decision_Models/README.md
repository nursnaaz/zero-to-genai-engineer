# Session 17 — Decision Models (RLCD · Jev)

### An LLM that is right 95% of the time still cannot automate the job — unless it tells you which 5% is the guess.

---

**MISSING from S15:** Fine-tuning changes *how* a model talks. It still writes sentences, and its confidence is still something you cannot act on. This session is about a different class of model: typed decisions with calibrated probabilities. No prose. A number you can threshold.

| File | What it is |
|---|---|
| [Classroom deck](https://nursnaaz.github.io/zero-to-genai-engineer/17_Decision_Models/teaching_decks/teach_01_rlcd_jev.html) | **RLCD · Jev** — calibration, Brier score, parallel decisions, threshold gating, and the two public alternatives (Strands Decider 2B, OpenAI Decisions) |
| [`teaching_decks/README.md`](./teaching_decks/README.md) | How to open the deck |
| [`Jev/use_cases/`](./Jev/use_cases/) | 19 runnable Jev use cases (Easy → Advanced) |
| [`comparison/`](./comparison/) | Same 88 decisions on Jev, Strands Decider 2B, and OpenAI Decisions |

## Classroom

1. Open the HTML deck in Chrome (arrows / Page Down; dots on the right; hit **Play** where shown).
2. After the deck: pick any use case under [`Jev/use_cases/`](./Jev/use_cases/). Copy `Jev/.env.example` to `Jev/.env` and put your TypeSafe key in `JEV_KEY`.
3. Optional: the [`comparison/`](./comparison/) folder reruns three use cases on all three products.

## The idea in one line

| Need | Prefer |
|---|---|
| A sentence, a reply, a plan | **An LLM** (Claude, GPT, …) |
| A pick from a menu, with a usable confidence | **A decision model** (Jev, Strands Decider, OpenAI Decisions) |
| Automate the sure ones, escalate the rest | **Threshold gate** on that confidence |

← [Course README](../README.md) · [S15 Fine-Tuning](../15_LLM_Fine_Tuning/) · [S16 recap](../16_Full_Course_Recap/)
