"""
Use case 09 - Let Jev pick which skill to load.

Your task goes in, your skill names and descriptions are the menu, Jev picks
one. Always include a None option so it never forces a bad load.

The skills here are the REAL ones from this course (S12 Deep Agents and S13
Dining Bot), read off disk -- not invented for the demo.

Run:  python3 pick_skill.py
"""
import json, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _shared.jev_client import Jev, choice            # noqa: E402

HERE = Path(__file__).parent
REPO = Path(__file__).resolve().parents[4]      # .../zero-to-genai-engineer


def load_real_skills() -> dict[str, str]:
    """Read every SKILL.md in the course and pull its name + description."""
    skills: dict[str, str] = {}
    for p in sorted(REPO.glob("1[23]_*/skills/*/SKILL.md")):
        text = p.read_text(encoding="utf-8", errors="ignore")
        name = p.parent.name
        desc = ""
        m = re.search(r"^description:\s*(.+)$", text, re.M | re.I)
        if m:
            desc = m.group(1).strip().strip('"').strip("'")
        if not desc:                      # fall back to the first real line
            for line in text.splitlines():
                line = line.strip().lstrip("#").strip()
                if line and not line.startswith("---") and ":" not in line[:12]:
                    desc = line
                    break
        skills[name] = (desc or name)[:220]
    return skills


# Tasks a student might actually type, with the skill we expect.
TEST_TASKS = [
    ("Write me a cover letter for a data engineer role at a Dubai bank", "cover-letter"),
    ("Pull together a pack for tomorrow's leadership meeting", "meeting-pack"),
    ("We had an outage last night, write the root cause analysis", "rca-pack"),
    ("Prep me for a systems design interview next week", "interview-prep"),
    ("Build the quarterly business review deck for the client", "qbr-pack"),
    ("Generate an invoice for 12 hours of consulting at 400 AED", "invoice"),
    ("Turn these scribbles from the standup into proper notes", "meeting-notes"),
    ("Draft the onboarding checklist for our new joiner", "onboarding"),
    ("Write a tiny python function to parse this date format", "tiny-code"),
    ("Plan next week's operations for the restaurant", "weekly-ops-plan"),
    ("Which menu items are running low on stock this week", "stock-risk-brief"),
    ("Build the promo calendar for Ramadan", "promo-calendar-brief"),
    ("What is the capital of France", "none"),
    ("Delete all my files", "none"),
]


def main() -> None:
    skills = load_real_skills()
    print(f"Loaded {len(skills)} real skills from the course:")
    for n in skills:
        print(f"   - {n}")

    menu = dict(skills)
    menu["none"] = "No skill fits this task. Handle it normally."

    jev = Jev()
    answers = jev.ask_many(
        [({"task": t}, {"skill": choice("Which skill should be loaded for `task`?", menu)})
         for t, _ in TEST_TASKS])

    print(f"\n{'task':<52}{'picked':<22}{'expected':<22}conf  ok")
    print("-" * 108)
    hits = 0
    rows = []
    for (task, expected), ans in zip(TEST_TASKS, answers):
        a = ans["skill"]
        ok = a["choice"] == expected
        hits += ok
        rows.append({"task": task, "picked": a["choice"], "expected": expected,
                     "confidence": round(a["confidence"], 3), "correct": ok})
        print(f"{task[:50]:<52}{a['choice']:<22}{expected:<22}"
              f"{a['confidence']:.2f}  {'y' if ok else 'NO'}")

    print(f"\n{hits}/{len(TEST_TASKS)} correct = {100*hits/len(TEST_TASKS):.0f}%")
    print(jev.report("skill routing"))
    print(f"\nThis is the whole point: one {jev.stats()['avg_ms_per_call']:.0f}ms call "
          f"replaces loading {len(skills)} skill files into context to decide.")

    assert all(r["picked"] in menu for r in rows), "Jev picked a skill that does not exist"
    assert hits >= len(TEST_TASKS) * 0.7, f"routing accuracy too low: {hits}/{len(TEST_TASKS)}"
    (HERE / "data" / "skill_routing_results.json").write_text(json.dumps(rows, indent=2))


if __name__ == "__main__":
    main()
