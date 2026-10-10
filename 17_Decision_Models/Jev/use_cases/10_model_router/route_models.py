"""
Use case 10 - Let Jev pick the model, so you stop paying Opus prices for
"what's the file path".

Jev reads each prompt, scores how hard it is, and your code maps that to a
model tier. One sub-second call in front of every request.

Run:  python3 route_models.py
"""
import json, sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _shared.jev_client import Jev, score, noul       # noqa: E402

HERE = Path(__file__).parent

# Illustrative relative prices (Opus = 1.0) so we can show the saving.
# Replace with your real numbers before quoting this to anyone.
TIER_COST = {"haiku": 0.04, "sonnet": 0.20, "opus": 1.00}

QUESTIONS = {
    "difficulty": score("How hard is this coding `task` for an AI assistant?", [
        "Trivial: a lookup or a one-line edit, no reasoning needed.",
        "Simple: a small self-contained change with an obvious approach.",
        "Involved: needs care across a file or two, some judgement.",
        "Hard: multi-file design, debugging, or a plan with trade-offs.",
    ]),
    "needs_codebase": noul("Does `task` require reading several files to answer well?"),
}


def tier_for(difficulty: float, needs_codebase: float) -> str:
    """Our code owns the policy. Jev only supplies the two numbers."""
    if difficulty < 0.8 and needs_codebase < 0.5:
        return "haiku"
    if difficulty < 2.2:
        return "sonnet"
    return "opus"


def main() -> None:
    tasks = json.loads((HERE / "data" / "tasks.json").read_text())
    jev = Jev()
    answers = jev.ask_many([({"task": t["prompt"]}, QUESTIONS) for t in tasks])

    rows = []
    for t, a in zip(tasks, answers):
        d = a["difficulty"]["score"]
        n = a["needs_codebase"]["noul"]
        rows.append({**t, "difficulty": round(d, 2), "needs_codebase": round(n, 2),
                     "tier": tier_for(d, n), "confidence": round(a["difficulty"]["confidence"], 3)})
    print(jev.report(f"routed {len(tasks)} prompts"))

    print(f"\n{'prompt':<56}{'diff':<7}{'files?':<8}{'tier':<9}gold")
    print("-" * 88)
    for r in rows:
        print(f"{r['prompt'][:54]:<56}{r['difficulty']:<7}{r['needs_codebase']:<8}"
              f"{r['tier']:<9}{r['gold_tier']}")

    print(f"\nRouting mix: {dict(Counter(r['tier'] for r in rows))}")

    everything_opus = len(rows) * TIER_COST["opus"]
    routed = sum(TIER_COST[r["tier"]] for r in rows)
    print(f"\nRelative cost for these {len(rows)} prompts (Opus = 1.0 each):")
    print(f"  everything on Opus : {everything_opus:.2f}")
    print(f"  Jev-routed         : {routed:.2f}")
    print(f"  saving             : {100*(1-routed/everything_opus):.0f}%")
    print(f"  routing overhead   : {jev.stats()['avg_ms_per_call']:.0f}ms per request")

    # the expensive mistake is sending a HARD task to the cheapest model
    bad = [r for r in rows if r["gold_tier"] == "hard" and r["tier"] == "haiku"]
    print(f"\nHard tasks wrongly sent to the cheapest model: {len(bad)}")
    assert not bad, f"under-routed hard tasks: {[r['id'] for r in bad]}"
    (HERE / "data" / "routing_results.json").write_text(json.dumps(rows, indent=2))


if __name__ == "__main__":
    main()
