"""
Use case 03 - Tag competitor ads into a swipe file.

Three questions per ad, sent in ONE call: format, call to action, funnel stage.
That is the "speculative fan-out" idea -- batching questions is far cheaper
than three round trips.

Run:  python3 tag_ads.py
"""
import csv, json, sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _shared.jev_client import Jev, choice            # noqa: E402

HERE = Path(__file__).parent

QUESTIONS = {
    "format": choice("What format is this ad `copy`?", {
        "problem_solution": "Names a pain, then offers the product as the fix.",
        "social_proof":     "Leads with a customer result, case study or numbers.",
        "educational":      "Offers a guide, report, template or teaching content.",
        "demo_offer":       "Invites you to see the product: demo, video or walkthrough.",
        "urgency_offer":    "Discount, deadline or scarcity.",
    }),
    "cta": choice("What is the main call to action in `copy`?", {
        "start_trial":   "Sign up or start using it now, usually free.",
        "book_demo":     "Talk to a human, book a call or demo.",
        "download":      "Grab a resource: PDF, report, template.",
        "watch":         "Watch a video.",
        "read":          "Read an article, case study or thread.",
        "none":          "No clear action is requested.",
    }),
    "funnel_stage": choice("What funnel stage is `copy` aimed at?", {
        "awareness":     "Reaching people who do not know they have the problem.",
        "consideration": "Reaching people comparing options.",
        "conversion":    "Pushing a ready buyer to act now.",
    }),
}


def main() -> None:
    ads = json.loads((HERE / "data" / "ads.json").read_text())
    jev = Jev()
    answers = jev.ask_many([({"copy": a["copy"], "brand": a["brand"]}, QUESTIONS) for a in ads])

    rows = []
    for ad, ans in zip(ads, answers):
        rows.append({**ad,
                     "format": ans["format"]["choice"],
                     "cta": ans["cta"]["choice"],
                     "funnel_stage": ans["funnel_stage"]["choice"],
                     "min_confidence": round(min(ans[k]["confidence"] for k in QUESTIONS), 3)})
    print(jev.report(f"tagged {len(ads)} ads x 3 questions"))

    print(f"\n{'brand':<9}{'format':<19}{'cta':<13}{'stage':<15}conf")
    print("-" * 64)
    for r in rows:
        print(f"{r['brand']:<9}{r['format']:<19}{r['cta']:<13}{r['funnel_stage']:<15}{r['min_confidence']}")

    print("\nSwipe-file summary (what is working in this market):")
    for field in ("format", "cta", "funnel_stage"):
        print(f"  {field:<13}", dict(Counter(r[field] for r in rows).most_common()))

    out = HERE / "data" / "ads_tagged.csv"
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    assert all(r["funnel_stage"] in ("awareness","consideration","conversion") for r in rows)
    print(f"\nWrote {out.name} (CSV export, same as the extension button would)")


if __name__ == "__main__":
    main()
