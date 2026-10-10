# Three decision models, head to head

Same three use cases, same states, same options, same gold labels. 88 decisions each.

```bash
python3 benchmark.py        # reruns everything, writes results.json
```

| | what it is | where it ran |
|---|---|---|
| **Jev** | TypeSafe `jev-latest`, hosted | `api.typesafe.ai`, over the internet |
| **Strands Decider 2B** | AWS open source, Apache-2.0, Qwen3.5-2B + LoRA + pointer head | **locally on this M2 Pro**, MPS |
| **Luna** | OpenAI Decisions API, `gpt-6-luna` | `api.openai.com/v1/decisions` |

Tasks: UC02 customer triage (60 tickets, 4-option choice), UC09 skill picker
(14 tasks, 13-option choice over this course's real skills), UC12 AI slop filter
(14 posts, yes/no).

---

## Results

| system | accuracy | 95% CI | p50 | p95 | input tok/decision | cost for 88 |
|---|---|---|---|---|---|---|
| Jev | 82/88 = **93.2%** | 85.9–96.8% | 354ms | 448ms | 464 | not published per-token |
| Strands 2B | 81/88 = **92.0%** | 84.5–96.1% | 273ms | 881ms | 200 | free (your hardware) |
| Luna | 85/88 = **96.6%** | 90.5–98.8% | 211ms | 302ms | 251 | **$0.0022** |

### Per use case

| use case | Jev | Strands | Luna |
|---|---|---|---|
| UC02 triage (60) | 91.7% | 93.3% | **98.3%** |
| UC09 skills (14) | **92.9%** | **92.9%** | 85.7% |
| UC12 slop (14) | **100%** | 85.7% | **100%** |

---

## The honest headline: on accuracy these are indistinguishable

McNemar exact test on the paired results:

| pair | discordant | p | verdict |
|---|---|---|---|
| Jev vs Strands | 4 / 3 | 1.000 | not significant |
| Jev vs Luna | 1 / 4 | 0.375 | not significant |
| Strands vs Luna | 1 / 5 | 0.219 | not significant |

At 88 items the confidence intervals overlap heavily. **Do not teach "Luna is more
accurate than Jev" from this.** Three systems disagreed on only 7 of 74 choice
decisions. What this benchmark actually shows is that all three are in the same
accuracy band, and the interesting differences are elsewhere.

---

## Where the real differences are

**Confidence works as a gate on all three.** This is the most useful finding.

| system | n ≥ 0.8 conf | accuracy there | n < 0.8 | accuracy there |
|---|---|---|---|---|
| Jev | 66 | 98.5% | 8 | **37.5%** |
| Strands | 48 | 97.9% | 26 | 84.6% |
| Luna | 59 | 100.0% | 15 | 80.0% |

Jev's confidence separates hardest: below 0.8 it is right barely a third of the
time, which is exactly what you want from a signal you route on. All three justify
the "send the unsure ones to a human" habit.

**Billing shape differs more than price.** Jev charged **464 input tokens per
decision**, Strands 200, Luna 251 — Jev's prompt scaffolding is roughly double.
Luna bills input only (output tokens were literally 0 on every call) at $0.10/1M,
so 88 decisions cost a fifth of a cent. Strands costs nothing per call because
you own the hardware.

**Strands scales with task size, as documented.** 273ms on the 4-option triage,
but **866ms p50** on the 13-option skill picker. The official blog says latency
"increases approximately linearly with task size" and quotes ~153ms for small
tasks on an M3 MacBook; ~270ms on this M2 Pro for small tasks is consistent, so
the local setup is behaving as intended, not misconfigured.

**A 2B model on a laptop held its own.** Strands matched Jev on the skill picker
and came within a few items overall, running on consumer hardware with no network
and no bill. For a course where students must not need a GPU, that matters.

---

## Caveats you must state if you teach this

1. **Latency is not apples to apples.** Jev and Luna are network round trips from
   Dubai; Strands is localhost with no network but slow hardware. A hosted Strands
   on a GPU would look very different (their RTX 3090 figure is ~115ms).
2. **88 decisions is small.** One run, no repeats, no variance estimate across runs.
3. **The data is mine.** Synthetic tickets and posts, plus this course's real skills.
   Results on your own traffic will differ.
4. **Vocabulary differs between APIs** even though the ideas match: Jev and Strands
   use `state` / `questions{}` / `noul`; Luna uses `input` / `questions[]` / `predicate`.
   Only choice and score carry confidence in all three; yes/no questions never do.

---

## Files

- `deciders.py` — one interface, three backends
- `benchmark.py` — the run
- `results.json` — every decision, latency and token count
- `strands_server.log` — local model server log

← [S17 Decision Models](../)
