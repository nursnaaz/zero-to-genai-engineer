# Classroom slides · Session 17 · Decision Models

**One presentation:** [teach_01_rlcd_jev.html](https://nursnaaz.github.io/zero-to-genai-engineer/17_Decision_Models/teaching_decks/teach_01_rlcd_jev.html)

Open in Chrome. Arrows / Page Down, or click the dots on the right. Hit Play and drag the sliders.

Includes: why overconfident LLMs can't automate, calibration and reliability diagrams, RLHF vs RLVR vs RLCD, the Brier score as a reward, one training step, the open OpenJev-RLCD recipe, autoregressive vs parallel decisions, what is known and unknown about Jev's architecture, the confidence formula, threshold gating in production, and the two public alternatives (Strands Decider 2B and OpenAI Decisions).

The last two slides are **measured, not claimed**: the same three use cases run head to head against Jev, Strands Decider 2B (locally on an M2 Pro) and OpenAI's Decisions API, 88 decisions each, with a significance test and the confidence-gate separation. Rerun the numbers with `python3 ../comparison/benchmark.py`.

**Teaching:** [SPEAKER_SCRIPT.md](./SPEAKER_SCRIPT.md) is a slide-by-slide script for all 21 slides. Each slide has the one idea, words you can speak, which controls to click, and the questions students ask. Four slides carry an 'understand it yourself first' box with the maths worked out: calibration (s4), the Brier score (s7), why honesty wins (s9) and the confidence formula (s14).
