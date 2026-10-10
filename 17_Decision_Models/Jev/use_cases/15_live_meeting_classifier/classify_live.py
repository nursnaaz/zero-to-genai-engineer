"""
Use case 15 - A live checker for what people say.

Every sentence gets sorted the moment it is spoken: decision, action item,
risk, question or none. A frontier model is far too slow to keep up with
speech. Jev answers in a few hundred milliseconds, so the notes build
themselves while the meeting is still running.

Run:  python3 classify_live.py
"""
import json, sys, time
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _shared.jev_client import Jev, choice            # noqa: E402

HERE = Path(__file__).parent
SPEECH_RATE_S = 3.5          # a spoken sentence takes roughly this long

QUESTION = {"kind": choice("What kind of statement is `sentence` in a work meeting?", {
    "decision": "A choice the group has settled on.",
    "action":   "Something a named person will go and do.",
    "risk":     "A worry about what could go wrong.",
    "question": "An open question that was asked.",
    "none":     "Chat, acknowledgement or a plain factual answer.",
})}


def main() -> None:
    sentences = json.loads((HERE / "data" / "meeting.json").read_text())
    jev = Jev()

    buckets = defaultdict(list)
    correct = 0
    print("Transcribing live...\n")
    for s in sentences:
        t0 = time.perf_counter()
        ans = jev.ask({"sentence": s["text"]}, QUESTION)["kind"]
        ms = (time.perf_counter() - t0) * 1000
        kind = ans["choice"]
        correct += kind == s["gold"]
        if kind != "none":
            buckets[kind].append(s["text"])
        flag = "" if kind == s["gold"] else f"   (expected {s['gold']})"
        keeps_up = "ok" if ms < SPEECH_RATE_S * 1000 else "TOO SLOW"
        print(f"  [{kind:<8} {ans['confidence']:.2f}] {ms:>5.0f}ms {keeps_up}  "
              f"{s['text'][:58]}{flag}")

    print(f"\n{'='*70}\nLIVE MEETING NOTES\n{'='*70}")
    for kind, title in (("decision", "Decisions"), ("action", "Action items"),
                        ("risk", "Risks"), ("question", "Open questions")):
        print(f"\n{title}")
        for line in buckets[kind] or ["  (none)"]:
            print(f"  - {line}" if buckets[kind] else line)

    acc = correct / len(sentences)
    st = jev.stats()
    print(f"\nAccuracy vs the human labels: {correct}/{len(sentences)} = {100*acc:.0f}%")
    print(f"Average {st['avg_ms_per_call']:.0f}ms per sentence. People speak a "
          f"sentence roughly every {SPEECH_RATE_S}s, so this keeps up with "
          f"{SPEECH_RATE_S*1000/st['avg_ms_per_call']:.0f}x headroom.")
    assert st["avg_ms_per_call"] < SPEECH_RATE_S * 1000, "cannot keep up with speech"
    assert acc >= 0.7, f"accuracy too low: {acc:.2f}"


if __name__ == "__main__":
    main()
