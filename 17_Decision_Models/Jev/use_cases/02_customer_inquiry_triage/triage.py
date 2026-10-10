"""
Use case 02 - Triage customer inquiries with a confidence cut-off.

Jev tags each message AND says how sure it is. Anything below the threshold
goes to a human instead of an automation. The threshold is one constant so you
can tune it as you learn what your business tolerates.

Run:  python3 triage.py            (uses the default 0.60 cut-off)
      python3 triage.py 0.80       (stricter: more goes to humans)
"""
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _shared.jev_client import Jev, choice            # noqa: E402

HERE = Path(__file__).parent

CONFIDENCE_THRESHOLD = 0.60      # <- the number the guide tells you to tune

CATEGORIES = {
    "billing": "Charges, invoices, refunds, payments, pricing of an existing account.",
    "bug":     "Something in the product is broken or behaving incorrectly.",
    "how-to":  "The customer is asking how to do something that already works.",
    "other":   "Anything else: feedback, partnerships, recruitment, off-topic.",
}

# Where each category goes when Jev is confident enough to automate it.
WORKFLOWS = {
    "billing": "billing-automation",
    "bug":     "create-jira-ticket",
    "how-to":  "send-help-article",
    "other":   "general-inbox",
}


def triage(tickets: list[dict], threshold: float) -> list[dict]:
    jev = Jev()
    q = {"category": choice("Which category is `message`?", CATEGORIES)}
    answers = jev.ask_many([({"message": t["message"]}, q) for t in tickets])

    out = []
    for t, ans in zip(tickets, answers):
        a = ans["category"]
        conf = a["confidence"]
        automated = conf >= threshold
        out.append({
            **t,
            "jev_label": a["choice"],
            "confidence": round(conf, 3),
            "route": WORKFLOWS[a["choice"]] if automated else "HUMAN-REVIEW",
            "automated": automated,
        })
    print(jev.report(f"triaged {len(tickets)}"))
    return out


def main() -> None:
    threshold = float(sys.argv[1]) if len(sys.argv) > 1 else CONFIDENCE_THRESHOLD
    tickets = json.loads((HERE / "data" / "tickets_labelled.json").read_text())
    results = triage(tickets, threshold)

    auto = [r for r in results if r["automated"]]
    human = [r for r in results if not r["automated"]]
    correct_auto = sum(r["jev_label"] == r["gold_label"] for r in auto)
    correct_all = sum(r["jev_label"] == r["gold_label"] for r in results)

    print(f"\nThreshold {threshold:.2f}")
    print(f"  automated     {len(auto):>3}/{len(results)}  "
          f"accuracy on those: {correct_auto}/{len(auto)} "
          f"= {100*correct_auto/len(auto):.1f}%" if auto else "  automated 0")
    print(f"  sent to human {len(human):>3}/{len(results)}")
    print(f"  overall accuracy (ignoring routing): "
          f"{correct_all}/{len(results)} = {100*correct_all/len(results):.1f}%")
    print(f"  routes used: {dict(Counter(r['route'] for r in results))}")

    wrong_and_confident = [r for r in auto if r["jev_label"] != r["gold_label"]]
    if wrong_and_confident:
        print(f"\n  {len(wrong_and_confident)} automated BUT wrong (the ones that cost you):")
        for r in wrong_and_confident:
            print(f"    [{r['confidence']}] said {r['jev_label']:<8} "
                  f"gold {r['gold_label']:<8} | {r['message'][:60]}")

    (HERE / "data" / "triage_results.json").write_text(json.dumps(results, indent=2))
    print(f"\nWrote data/triage_results.json")


if __name__ == "__main__":
    main()
