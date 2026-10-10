"""
Head to head on three of the 19 use cases, with gold labels for all three.

  UC02 customer triage   60 tickets   choice, 4 options
  UC09 skill picker      14 tasks     choice, 13 options (this course's real skills)
  UC12 AI slop filter    14 posts     noul

Everything runs SEQUENTIALLY so the latency numbers are single-request latency
and not distorted by concurrency.
"""
import json, re, statistics, sys, time
from pathlib import Path

sys.path.insert(0, ".")
from deciders import JevDecider, StrandsDecider, LunaDecider

UC = Path(__file__).resolve().parents[1] / "Jev" / "use_cases"
REPO = Path(__file__).resolve().parents[2]
OUT = Path(__file__).parent


# ----------------------------------------------------------------- tasks
def task_triage():
    rows = json.loads((UC / "02_customer_inquiry_triage/data/tickets_labelled.json").read_text())
    opts = {
        "billing": "Charges, invoices, refunds, payments, pricing of an existing account.",
        "bug":     "Something in the product is broken or behaving incorrectly.",
        "how-to":  "The customer is asking how to do something that already works.",
        "other":   "Anything else: feedback, partnerships, recruitment, off-topic.",
    }
    return ("UC02 customer triage", "choice",
            [({"message": r["message"]}, r["gold_label"]) for r in rows],
            "Which category is `message`?", opts, None)


def task_skills():
    skills = {}
    for p in sorted(REPO.glob("1[23]_*/skills/*/SKILL.md")):
        t = p.read_text(encoding="utf-8", errors="ignore")
        m = re.search(r"^description:\s*(.+)$", t, re.M | re.I)
        skills[p.parent.name] = (m.group(1).strip().strip('"') if m else p.parent.name)[:200]
    skills["none"] = "No skill fits this task."
    tasks = [
        ("Write me a cover letter for a data engineer role at a Dubai bank", "cover-letter"),
        ("Pull together a pack for tomorrow's leadership meeting", "meeting-pack"),
        ("We had an outage last night, write the root cause analysis", "rca-pack"),
        ("Prep me for a systems design interview next week", "interview-prep"),
        ("Build the quarterly business review deck for the client", "qbr-pack"),
        ("Generate an invoice for 12 hours of consulting at 400 AED", "invoice"),
        ("Turn these scribbles from the standup into proper notes", "meeting-notes"),
        ("Draft the onboarding checklist for our new joiner", "onboarding"),
        ("Write a tiny python function to parse this date format", "tiny-code"),
        ("Plan next week's operations for the restaurant", "weekly-ops-plan"),
        ("Which menu items are running low on stock this week", "stock-risk-brief"),
        ("Build the promo calendar for Ramadan", "promo-calendar-brief"),
        ("What is the capital of France", "none"),
        ("Delete all my files", "none"),
    ]
    return ("UC09 skill picker", "choice",
            [({"task": t}, g) for t, g in tasks],
            "Which skill should be loaded for `task`?", skills, None)


def task_slop():
    rows = json.loads((UC / "12_ai_slop_filter/data/posts.json").read_text())
    crit = {"true": "Generic hype, emoji spam, listicle padding, hollow motivational phrasing.",
            "false": "A specific first-hand observation, number, incident or opinion."}
    return ("UC12 AI slop filter", "noul",
            [({"post": r["text"]}, r["gold"]) for r in rows],
            "Is this `post` low-effort AI-generated engagement bait?", None, crit)


TASKS = [task_triage(), task_skills(), task_slop()]


def run(decider, label, kind, items, instructions, options, criteria):
    recs = []
    for i, (state, gold) in enumerate(items, 1):
        try:
            a = (decider.choice(state, instructions, options) if kind == "choice"
                 else decider.noul(state, instructions, criteria))
            pred = a.pick if kind == "choice" else ("slop" if a.prob >= 0.5 else "human")
            recs.append({"gold": gold, "pred": pred, "conf": a.confidence,
                         "ms": a.latency_ms, "in": a.input_tokens, "out": a.output_tokens,
                         "correct": pred == gold})
        except Exception as e:
            recs.append({"gold": gold, "pred": None, "conf": 0.0, "ms": 0,
                         "in": 0, "out": 0, "correct": False, "error": str(e)[:120]})
        print(f"\r    {decider.name:<8} {label:<22} {i}/{len(items)}", end="", flush=True)
    print()
    return recs


def summarise(recs, decider):
    ok = [r for r in recs if r.get("error") is None]
    acc = sum(r["correct"] for r in recs) / len(recs)
    lat = sorted(r["ms"] for r in ok) or [0]
    tin = sum(r["in"] for r in recs); tout = sum(r["out"] for r in recs)
    cost = decider.cost(tin, tout) if hasattr(decider, "cost") else None
    # accuracy on the slice the system was confident about
    conf80 = [r for r in recs if r["conf"] >= 0.8]
    return {"n": len(recs), "accuracy": acc,
            "p50_ms": statistics.median(lat), "p95_ms": lat[int(len(lat) * 0.95) - 1],
            "in_tokens": tin, "out_tokens": tout, "cost_usd": cost,
            "n_conf80": len(conf80),
            "acc_conf80": (sum(r["correct"] for r in conf80) / len(conf80)) if conf80 else None,
            "errors": sum(1 for r in recs if r.get("error"))}


def main():
    deciders = [JevDecider(), StrandsDecider(), LunaDecider()]
    report = {}
    for label, kind, items, instructions, options, criteria in TASKS:
        print(f"\n{label}  ({len(items)} items, {kind})")
        report[label] = {}
        for d in deciders:
            t0 = time.perf_counter()
            recs = run(d, label, kind, items, instructions, options, criteria)
            s = summarise(recs, d)
            s["wall_s"] = round(time.perf_counter() - t0, 1)
            report[label][d.name] = {"summary": s, "records": recs}
            c = f"${s['cost_usd']:.5f}" if s["cost_usd"] is not None else "n/a"
            print(f"      acc {s['accuracy']*100:5.1f}%   p50 {s['p50_ms']:6.0f}ms   "
                  f"p95 {s['p95_ms']:6.0f}ms   tok {s['in_tokens']}/{s['out_tokens']}   "
                  f"cost {c}   errors {s['errors']}")
    (OUT / "results.json").write_text(json.dumps(report, indent=2))
    print(f"\nWrote results.json")


if __name__ == "__main__":
    main()
