"""
Use case 08 - Verify Jev before you trust it.

This is the one that makes every other use case defensible.

Method, exactly as the guide describes it:
  1. Take examples a human already labelled.
  2. Split in half. TUNE on the first half, REPORT only on the second.
     (Reporting on data you tuned against is how people fool themselves.)
  3. Compare Jev's answer with the human label.
  4. Show accuracy AT EACH CONFIDENCE LEVEL -- that is what tells you where
     to set your automation threshold.

Run:  python3 validate.py
"""
import json, sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _shared.jev_client import Jev, choice            # noqa: E402

HERE = Path(__file__).parent
DATA = HERE.parent / "02_customer_inquiry_triage" / "data" / "tickets_labelled.json"

# --- version A: the first thing anyone writes (bare category names) ---
CATS_V1 = {"billing": "billing", "bug": "bug", "how-to": "how-to", "other": "other"}

# --- version B: tuned on the TUNE half after looking at the mistakes ---
CATS_V2 = {
    "billing": "Anything about money on an existing account: charges, invoices, "
               "refunds, double payments, receipts, VAT, currency, renewals, discounts.",
    "bug":     "The product is broken or behaving incorrectly: errors, crashes, "
               "blank screens, things that silently fail.",
    "how-to":  "Asking how to use or configure something that already works, "
               "including questions comparing plan features.",
    "other":   "Not about the product working or money owed: feedback, partnerships, "
               "recruitment, press, unsubscribe requests, off-topic.",
}


def run(tickets, cats, jev):
    q = {"category": choice("Which category is `message`?", cats)}
    answers = jev.ask_many([({"message": t["message"]}, q) for t in tickets])
    out = []
    for t, a in zip(tickets, answers):
        c = a["category"]
        out.append({**t, "pred": c["choice"], "conf": c["confidence"],
                    "correct": c["choice"] == t["gold_label"]})
    return out


def accuracy(rows):
    return sum(r["correct"] for r in rows) / len(rows) if rows else 0.0


def by_confidence(rows):
    """Accuracy inside each confidence band -- the table that sets your threshold."""
    bands = [(0.0, 0.5), (0.5, 0.7), (0.7, 0.9), (0.9, 1.01)]
    print(f"\n  {'confidence band':<18}{'n':<6}{'accuracy':<11}cumulative if you automate above the band")
    print("  " + "-" * 82)
    for lo, hi in bands:
        band = [r for r in rows if lo <= r["conf"] < hi]
        above = [r for r in rows if r["conf"] >= lo]
        if not band:
            print(f"  {f'{lo:.1f} - {hi:.2f}':<18}{'0':<6}{'-':<11}")
            continue
        print(f"  {f'{lo:.1f} - {hi:.2f}':<18}{len(band):<6}"
              f"{accuracy(band)*100:>6.1f}%    "
              f"automate {len(above):>2}/{len(rows)} at {accuracy(above)*100:.1f}% accuracy")


def confusion(rows, labels):
    m = defaultdict(Counter)
    for r in rows:
        m[r["gold_label"]][r["pred"]] += 1
    print(f"\n  rows = human label, columns = Jev")
    print("  " + " " * 10 + "".join(f"{l:<10}" for l in labels))
    for g in labels:
        print(f"  {g:<10}" + "".join(
            f"{m[g][p] if m[g][p] else '.':<10}" for p in labels))


def main() -> None:
    tickets = json.loads(DATA.read_text())
    mid = len(tickets) // 2
    tune, report = tickets[:mid], tickets[mid:]
    print(f"{len(tickets)} labelled examples -> {len(tune)} to tune on, "
          f"{len(report)} held back for the score")

    jev = Jev()
    labels = ["billing", "bug", "how-to", "other"]

    print("\n" + "=" * 86)
    print("STEP 1  Bare category names, measured on the TUNE half")
    print("=" * 86)
    tune_v1 = run(tune, CATS_V1, jev)
    print(f"  accuracy {accuracy(tune_v1)*100:.1f}%")
    print("  mistakes that told us what to fix:")
    for r in tune_v1:
        if not r["correct"]:
            print(f"    [{r['conf']:.2f}] said {r['pred']:<8} gold {r['gold_label']:<8} "
                  f"| {r['message'][:54]}")

    print("\n" + "=" * 86)
    print("STEP 2  Descriptions rewritten from those mistakes, still on the TUNE half")
    print("=" * 86)
    tune_v2 = run(tune, CATS_V2, jev)
    print(f"  accuracy {accuracy(tune_v2)*100:.1f}%  "
          f"(was {accuracy(tune_v1)*100:.1f}%)")

    print("\n" + "=" * 86)
    print("STEP 3  THE HONEST NUMBER: tuned version on the half we never looked at")
    print("=" * 86)
    rep_v1 = run(report, CATS_V1, jev)
    rep_v2 = run(report, CATS_V2, jev)
    print(f"  bare names : {accuracy(rep_v1)*100:.1f}%")
    print(f"  tuned      : {accuracy(rep_v2)*100:.1f}%   <- report this one")

    by_confidence(rep_v2)
    confusion(rep_v2, labels)

    print("\n" + "=" * 86)
    print("STEP 4  What threshold should you actually use?")
    print("=" * 86)
    for t in (0.5, 0.6, 0.7, 0.8, 0.9):
        auto = [r for r in rep_v2 if r["conf"] >= t]
        if not auto:
            continue
        wrong = sum(not r["correct"] for r in auto)
        print(f"  threshold {t:.1f}  ->  automate {len(auto):>2}/{len(rep_v2)} "
              f"({100*len(auto)/len(rep_v2):>3.0f}%), "
              f"{wrong} of them wrong, automated accuracy {accuracy(auto)*100:.1f}%")

    print(f"\n{jev.report('total')}")

    (HERE / "data" / "validation_report.json").write_text(json.dumps({
        "tune_bare": accuracy(tune_v1), "tune_tuned": accuracy(tune_v2),
        "holdout_bare": accuracy(rep_v1), "holdout_tuned": accuracy(rep_v2),
        "rows": rep_v2}, indent=2))

    assert accuracy(rep_v2) >= 0.75, "held-out accuracy below the bar we would ship at"
    print("Wrote data/validation_report.json")


if __name__ == "__main__":
    main()
