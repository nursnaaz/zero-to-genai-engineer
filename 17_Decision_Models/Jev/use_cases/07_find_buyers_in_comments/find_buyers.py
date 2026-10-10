"""
Use case 07 - Find the buyers hiding in your comments.

Your buyers are already in the comments, buried between the emojis. Jev tags
each one so you get a priority list instead of scrolling.

In production you would pull comments with Apify. Here we use a saved export
so the use case is runnable and testable offline.

Run:  python3 find_buyers.py
"""
import json, sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _shared.jev_client import Jev, choice, noul      # noqa: E402

HERE = Path(__file__).parent

QUESTIONS = {
    "bucket": choice("How should this `comment` be handled?", {
        "ready_to_buy": "Shows real purchase intent: asking price, stock, shipping, how to order, or saying they want it.",
        "question":     "Asking for product information without clear buying intent yet.",
        "complaint":    "Unhappy: a problem with an order, the product, or the service.",
        "other":        "Everything else: praise, jokes, emojis, off-topic.",
    }),
    "needs_reply": noul("Does this `comment` need a human reply to win or keep a sale?"),
}

PRIORITY = {"ready_to_buy": 0, "complaint": 1, "question": 2, "other": 3}


def main() -> None:
    comments = json.loads((HERE / "data" / "comments.json").read_text())
    jev = Jev()
    answers = jev.ask_many([({"comment": c["text"]}, QUESTIONS) for c in comments])

    rows = []
    for c, a in zip(comments, answers):
        rows.append({**c,
                     "bucket": a["bucket"]["choice"],
                     "confidence": round(a["bucket"]["confidence"], 3),
                     "needs_reply": round(a["needs_reply"]["noul"], 3)})
    print(jev.report(f"tagged {len(comments)} comments"))

    rows.sort(key=lambda r: (PRIORITY[r["bucket"]], -r["needs_reply"]))
    print(f"\nWork queue, buyers first:\n")
    print(f"{'bucket':<14}{'reply?':<8}{'conf':<7}comment")
    print("-" * 78)
    for r in rows[:22]:
        print(f"{r['bucket']:<14}{r['needs_reply']:<8}{r['confidence']:<7}{r['text'][:44]}")
    print(f"   ... {len(rows)-22} more")

    counts = Counter(r["bucket"] for r in rows)
    print(f"\nBuckets: {dict(counts)}")
    buyers = [r for r in rows if r["bucket"] == "ready_to_buy"]
    print(f"{len(buyers)} ready-to-buy comments surfaced out of {len(rows)} "
          f"({100*len(buyers)/len(rows):.0f}% of the pile) -- that is the list you action today.")

    # a loose sanity check against the hand hints in the data
    hinted_buyers = {c["id"] for c in comments if c["gold_hint"] == "C"}
    found = {r["id"] for r in buyers}
    recall = len(hinted_buyers & found) / len(hinted_buyers)
    print(f"Recall against hand-marked buyers: {len(hinted_buyers & found)}/{len(hinted_buyers)} "
          f"= {100*recall:.0f}%")
    assert recall >= 0.6, f"buyer recall too low: {recall:.2f}"

    (HERE / "data" / "comments_tagged.json").write_text(json.dumps(rows, indent=2))


if __name__ == "__main__":
    main()
