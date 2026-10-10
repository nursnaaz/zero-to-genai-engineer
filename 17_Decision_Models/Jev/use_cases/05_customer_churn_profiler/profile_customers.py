"""
Use case 05 - Score and profile your customer base.

Jev reads the account facts you already have and scores churn risk 1-10,
then buckets each customer. Note what we are NOT doing: we are not asking Jev
to "analyse the customer". We ask one narrow question it can answer in a
fraction of a second, and we do the bucketing in code.

Run:  python3 profile_customers.py
"""
import csv, json, sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _shared.jev_client import Jev, score, choice     # noqa: E402

HERE = Path(__file__).parent

QUESTIONS = {
    "churn_risk": score(
        "Based on this account's facts, how likely is this customer to cancel soon?", [
        "Very unlikely: engaged, committed, no warning signs.",
        "Unlikely: healthy with a minor concern.",
        "Possible: some disengagement or friction.",
        "Likely: several clear warning signs.",
        "Very likely: actively disengaging or already cancelling.",
    ]),
    "primary_signal": choice("What is the strongest churn signal in this account?", {
        "started_cancellation": "They have already begun cancelling.",
        "inactive":             "They have not logged in for a long time.",
        "unresolved_support":   "They have several open tickets.",
        "short_tenure":         "They are new and not yet established.",
        "none":                 "No meaningful warning signal.",
    }),
}

def bucket(risk_0_4: float) -> str:
    """Our code owns the thresholds, not the model."""
    if risk_0_4 >= 3.0:   return "At risk"
    if risk_0_4 >= 1.75:  return "Needs attention"
    return "Healthy"


def main() -> None:
    rows = list(csv.DictReader(open(HERE / "data" / "customers.csv")))
    jev = Jev()
    answers = jev.ask_many([(r, QUESTIONS) for r in rows])

    for r, a in zip(rows, answers):
        raw = a["churn_risk"]["score"]              # 0..4 across our 5 levels
        r["churn_score_0_4"] = round(raw, 2)
        r["churn_score_1_10"] = round(1 + raw * 9 / 4, 1)   # rescale for the business
        r["segment"] = bucket(raw)
        r["signal"] = a["primary_signal"]["choice"]
        r["confidence"] = round(a["churn_risk"]["confidence"], 3)
    print(jev.report(f"profiled {len(rows)} customers"))

    rows.sort(key=lambda r: -r["churn_score_0_4"])
    print(f"\n{'id':<7}{'score':<7}{'segment':<17}{'signal':<22}{'tenure':<8}{'idle':<6}cancelling")
    print("-" * 78)
    for r in rows[:15]:
        print(f"{r['customer_id']:<7}{r['churn_score_1_10']:<7}{r['segment']:<17}"
              f"{r['signal']:<22}{r['tenure_months']:<8}{r['days_since_last_login']:<6}"
              f"{r['started_cancellation']}")
    print(f"   ... {len(rows)-15} more, sorted at-risk first")

    print("\nSegments:", dict(Counter(r["segment"] for r in rows)))

    # sanity: anyone actively cancelling must not be called Healthy
    cancelling = [r for r in rows if r["started_cancellation"] == "True"]
    bad = [r for r in cancelling if r["segment"] == "Healthy"]
    print(f"Accounts already cancelling: {len(cancelling)}, "
          f"of which wrongly 'Healthy': {len(bad)}")
    assert not bad, f"cancelling accounts marked Healthy: {[r['customer_id'] for r in bad]}"

    out = HERE / "data" / "customers_scored.csv"
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    print(f"Wrote {out.name}")


if __name__ == "__main__":
    main()
