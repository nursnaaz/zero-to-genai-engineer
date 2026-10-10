"""
Use case 04 - Score every possible clip in a long video, return the best ones.

Slide a window over the transcript to build candidate 30-60s clips, then ask
Jev to SCORE each one. Scoring is the right shape here: "how good a short would
this make" is a spectrum, not a category.

Run:  python3 find_clips.py
"""
import json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _shared.jev_client import Jev, score, noul       # noqa: E402

HERE = Path(__file__).parent
MIN_S, MAX_S, TOP_N = 25, 60, 5


def build_candidates(sentences: list[dict]) -> list[dict]:
    """Every contiguous run of sentences lasting MIN_S..MAX_S seconds."""
    out = []
    for i in range(len(sentences)):
        for j in range(i, len(sentences)):
            start, end = sentences[i]["start"], sentences[j]["end"]
            dur = end - start
            if dur < MIN_S:
                continue
            if dur > MAX_S:
                break
            out.append({"start": start, "end": end, "duration": dur,
                        "text": " ".join(s["text"] for s in sentences[i:j+1])})
    return out


def pick_non_overlapping(cands: list[dict], n: int, max_overlap: float = 0.25) -> list[dict]:
    """Greedy non-maximum suppression.

    Without this you get five versions of the same moment: the scores are all
    high around one good passage, so the naive top-N is useless to a human.
    Take the best clip, drop anything overlapping it too much, repeat.
    """
    chosen: list[dict] = []
    for c in sorted(cands, key=lambda x: -x["rank_score"]):
        clash = False
        for k in chosen:
            overlap = min(c["end"], k["end"]) - max(c["start"], k["start"])
            if overlap > 0 and overlap / min(c["duration"], k["duration"]) > max_overlap:
                clash = True
                break
        if not clash:
            chosen.append(c)
        if len(chosen) == n:
            break
    return chosen


QUESTIONS = {
    "clip_quality": score("How well would `text` work as a standalone short video clip?", [
        "Weak: mid-conversation, needs context, no payoff.",
        "Okay: understandable alone but forgettable.",
        "Good: one clear idea with a satisfying point.",
        "Excellent: a self-contained hook and a quotable payoff.",
    ]),
    "standalone": noul("Does `text` make sense without any earlier context?"),
}


def main() -> None:
    sentences = json.loads((HERE / "data" / "transcript.json").read_text())
    candidates = build_candidates(sentences)
    print(f"{len(sentences)} sentences -> {len(candidates)} candidate clips "
          f"({MIN_S}-{MAX_S}s)")

    jev = Jev()
    answers = jev.ask_many([({"text": c["text"]}, QUESTIONS) for c in candidates])
    for c, a in zip(candidates, answers):
        c["quality"] = a["clip_quality"]["score"]
        c["confidence"] = a["clip_quality"]["confidence"]
        c["standalone"] = a["standalone"]["noul"]
        # rank on quality, but a clip that needs context is worth less
        c["rank_score"] = c["quality"] * (0.5 + 0.5 * c["standalone"])
    print(jev.report(f"scored {len(candidates)} clips"))

    best = pick_non_overlapping(candidates, TOP_N)
    print(f"\nTop {TOP_N} clips to post:")
    for n, c in enumerate(best, 1):
        mm = lambda s: f"{s//60}:{s%60:02d}"
        print(f"\n{n}. {mm(c['start'])}-{mm(c['end'])}  ({c['duration']}s)  "
              f"quality {c['quality']:.2f}  standalone {c['standalone']:.2f}")
        print(f"   {c['text'][:150]}{'...' if len(c['text'])>150 else ''}")

    (HERE / "data" / "top_clips.json").write_text(json.dumps(best, indent=2))
    assert all(0 <= c["quality"] <= 3 for c in candidates), "score outside level range"
    print(f"\nWrote data/top_clips.json")


if __name__ == "__main__":
    main()
