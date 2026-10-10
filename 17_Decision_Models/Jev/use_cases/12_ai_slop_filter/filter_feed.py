"""
Use case 12 - Fold away AI slop in a feed.

One noul per post as it loads. Fold it if Jev is over 80% sure, with a button
to show it anyway. This file is the testable core; ./extension/ holds the real
Chrome extension that calls the same API.

Run:  python3 filter_feed.py
"""
import json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _shared.jev_client import Jev, noul              # noqa: E402

HERE = Path(__file__).parent
FOLD_AT = 0.80          # the guide's number: only fold when Jev is really sure

QUESTION = {"slop": noul(
    "Is this `post` low-effort AI-generated engagement bait?",
    true_means="Generic hype, listicle padding, emoji spam, hollow motivational "
               "phrasing, or thread-bait with no specific first-hand detail.",
    false_means="A specific first-hand observation, number, incident or opinion "
                "that only someone who did the work could write.")}


def main() -> None:
    posts = json.loads((HERE / "data" / "posts.json").read_text())
    jev = Jev()
    answers = jev.ask_many([({"post": p["text"]}, QUESTION) for p in posts])

    rows = []
    for p, a in zip(posts, answers):
        prob = a["slop"]["noul"]
        rows.append({**p, "slop_prob": round(prob, 3),
                     "folded": prob >= FOLD_AT})
    print(jev.report(f"screened {len(posts)} posts"))

    print(f"\n{'p(slop)':<10}{'folded':<9}{'gold':<8}post")
    print("-" * 96)
    for r in sorted(rows, key=lambda r: -r["slop_prob"]):
        print(f"{r['slop_prob']:<10}{'FOLD' if r['folded'] else 'show':<9}"
              f"{r['gold']:<8}{r['text'][:60]}")

    folded = [r for r in rows if r["folded"]]
    slop = [r for r in rows if r["gold"] == "slop"]
    caught = [r for r in folded if r["gold"] == "slop"]
    false_folds = [r for r in folded if r["gold"] == "human"]

    print(f"\nFolded {len(folded)}/{len(rows)} posts at the {FOLD_AT} threshold")
    print(f"  slop caught      : {len(caught)}/{len(slop)}")
    print(f"  genuine folded   : {len(false_folds)}   <- the error users hate most")
    print(f"  avg latency      : {jev.stats()['avg_ms_per_call']:.0f}ms per post, "
          f"so a feed stays responsive")

    assert not false_folds, f"hid real posts: {[r['id'] for r in false_folds]}"
    assert len(caught) >= len(slop) * 0.7, "caught too little slop to be useful"
    (HERE / "data" / "feed_results.json").write_text(json.dumps(rows, indent=2))


if __name__ == "__main__":
    main()
