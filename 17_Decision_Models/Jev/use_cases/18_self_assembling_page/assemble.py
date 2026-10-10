"""
Use case 18 - A landing page that builds itself per visitor.

Jev does not write the page. It PICKS which prebuilt sections to show and in
what order, which is why the page still renders at normal speed.

Run:  python3 assemble.py
"""
import json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _shared.jev_client import Jev, choice, score     # noqa: E402

HERE = Path(__file__).parent

SECTIONS = {
    "hero_explainer":  "Explains what the product is, for someone who has never heard of it.",
    "hero_returning":  "Welcome back panel with a continue-where-you-left-off button.",
    "pricing":         "Plan comparison and prices.",
    "testimonials":    "Customer quotes and logos.",
    "case_study":      "One detailed customer result with numbers.",
    "signin":          "Sign in form.",
    "upgrade_cta":     "Prompt to move from free to a paid plan.",
    "docs_quickstart": "Jump straight into the technical quickstart.",
    "newsletter":      "Email capture.",
}
SLOTS = 4


def main() -> None:
    visitors = json.loads((HERE / "data" / "visitors.json").read_text())
    jev = Jev()

    for v in visitors:
        profile = {
            "arrived_from": v["referrer"],
            "search_query": v["query"] or "none",
            "returning_visitor": v["returning"],
            "logged_in": v["logged_in"],
            "current_plan": v["plan"] or "not a customer",
        }
        # One score per section: how useful is it to THIS visitor?
        questions = {
            f"s_{name}": score(
                f"How useful is a '{desc}' section to this visitor right now?",
                ["Not useful at all.", "Marginal.", "Useful.", "Exactly what they need."])
            for name, desc in SECTIONS.items()
        }
        ans = jev.ask(profile, questions)

        ranked = sorted(((n, ans[f"s_{n}"]["score"]) for n in SECTIONS),
                        key=lambda x: -x[1])
        page = ranked[:SLOTS]

        bits = [f"{v['id']}  from {v['referrer']}"]
        if v["query"]:
            bits.append(f'searching "{v["query"]}"')
        bits.append("returning" if v["returning"] else "first visit")
        if v["logged_in"]:
            bits.append(f"logged in ({v['plan']})")
        print("\n" + " | ".join(bits))
        print("   page served:", " > ".join(n for n, _ in page))
        print("   scores:", ", ".join(f"{n} {s:.1f}" for n, s in page))

    print(f"\n{jev.report(f'assembled {len(visitors)} pages')}")
    st = jev.stats()
    print(f"{st['avg_ms_per_call']:.0f}ms to choose {SLOTS} of {len(SECTIONS)} sections, "
          f"which is inside a normal page load budget.")


if __name__ == "__main__":
    main()
