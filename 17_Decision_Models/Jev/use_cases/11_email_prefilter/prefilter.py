"""
Use case 11 - Put Jev in FRONT of your expensive agent.

Three cheap questions per email. Only the ones that need a reply reach Claude.
Your agent reads less, so your bill drops and it never sees the scams.

Run:  python3 prefilter.py
"""
import json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _shared.jev_client import Jev, noul              # noqa: E402

HERE = Path(__file__).parent

QUESTIONS = {
    "needs_reply": noul("Does this email need a personal reply from the recipient?",
                        true_means="A real person is waiting on an answer or decision.",
                        false_means="Automated, promotional, or purely informational."),
    "brand_deal":  noul("Is this email proposing a paid collaboration, sponsorship or partnership?"),
    "scam":        noul("Is this email a phishing attempt or a scam?"),
}

SCAM_BLOCK = 0.60       # above this we never forward, whatever else it says
REPLY_PASS = 0.50


def main() -> None:
    inbox = json.loads((HERE / "data" / "inbox.json").read_text())
    jev = Jev()
    answers = jev.ask_many(
        [({"subject": e["subject"], "body": e["body"]}, QUESTIONS) for e in inbox])

    rows = []
    for e, a in zip(inbox, answers):
        scam = a["scam"]["noul"]
        reply = a["needs_reply"]["noul"]
        brand = a["brand_deal"]["noul"]
        # order matters: a scam is dropped even if it looks like it wants a reply
        if scam >= SCAM_BLOCK:
            action = "BLOCK (scam)"
        elif brand >= 0.6:
            action = "brand-deal folder"
        elif reply >= REPLY_PASS:
            action = "-> Claude drafts a reply"
        else:
            action = "archive"
        rows.append({**e, "reply": round(reply, 2), "brand": round(brand, 2),
                     "scam": round(scam, 2), "action": action})
    print(jev.report(f"screened {len(inbox)} emails"))

    print(f"\n{'subject':<38}{'reply':<7}{'brand':<7}{'scam':<7}{'action':<26}gold")
    print("-" * 100)
    for r in rows:
        print(f"{r['subject'][:36]:<38}{r['reply']:<7}{r['brand']:<7}{r['scam']:<7}"
              f"{r['action']:<26}{r['gold']}")

    to_claude = [r for r in rows if r["action"].startswith("->")]
    print(f"\n{len(to_claude)}/{len(rows)} emails reach the expensive agent "
          f"({100*len(to_claude)/len(rows):.0f}%).")
    print(f"The other {len(rows)-len(to_claude)} were handled for the cost of a Jev call each.")

    # the two failures that actually matter
    scams_forwarded = [r for r in rows if r["gold"] == "scam" and r["action"].startswith("->")]
    missed_replies = [r for r in rows if r["gold"] == "reply" and not r["action"].startswith("->")]
    print(f"\nScams that reached the agent: {len(scams_forwarded)}  (must be 0)")
    print(f"Real replies wrongly dropped: {len(missed_replies)}  (must be 0)")
    for r in missed_replies:
        print(f"    MISSED: {r['subject']}")
    assert not scams_forwarded, "a scam got through to the agent"
    assert not missed_replies, "a genuine email needing a reply was dropped"
    (HERE / "data" / "prefilter_results.json").write_text(json.dumps(rows, indent=2))


if __name__ == "__main__":
    main()
