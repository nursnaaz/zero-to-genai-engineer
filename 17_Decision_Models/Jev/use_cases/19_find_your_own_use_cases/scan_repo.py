"""
Use case 19 - Find YOUR own Jev use cases.

Instead of pasting a website into Claude, this scans a real codebase for the
shape of work Jev replaces:

  * keyword / substring matching that stands in for understanding
  * long if / elif ladders branching on text
  * a general LLM call whose whole job is to return one label

Each candidate is then sent to Jev, which decides whether it is genuinely
replaceable and which primitive fits. Jev auditing code for Jev-shaped work.

Run:  python3 scan_repo.py
"""
import json, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _shared.jev_client import Jev, choice, noul      # noqa: E402

HERE = Path(__file__).parent
REPO = Path(__file__).resolve().parents[4]
SKIP = {".git", "node_modules", ".venv", ".kilo", ".kiro", "__pycache__",
        "reference", "17_Decision_Models"}       # skip ourselves

PATTERNS = [
    ("keyword_match",
     re.compile(r"\b(any|all)\s*\(\s*\w+\s+in\s+.{0,40}(lower\(\)|text|message|query|content)", re.I)),
    ("keyword_list",
     re.compile(r"^\s*[A-Z_]{3,}\s*=\s*\[\s*[\"'][a-z ]{3,}[\"']\s*,\s*[\"'][a-z ]{3,}[\"']", re.M)),
    ("elif_ladder_on_text",
     re.compile(r"elif\s+[\"'][\w ]+[\"']\s+in\s+\w+", re.I)),
    ("llm_for_a_label",
     re.compile(r"(classify|categor|intent|route|triage|sentiment|is_|detect)\w*\s*\(", re.I)),
]


def find_candidates(limit_per_file: int = 2) -> list[dict]:
    out = []
    for p in sorted(REPO.rglob("*.py")):
        if any(s in p.parts for s in SKIP):
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        lines = text.splitlines()
        found = 0
        for kind, rx in PATTERNS:
            for m in rx.finditer(text):
                if found >= limit_per_file:
                    break
                line_no = text[:m.start()].count("\n")
                snippet = "\n".join(lines[max(0, line_no - 3): line_no + 5])
                if len(snippet.strip()) < 40:
                    continue
                out.append({"file": str(p.relative_to(REPO)), "line": line_no + 1,
                            "pattern": kind, "snippet": snippet[:900]})
                found += 1
    return out


QUESTIONS = {
    "replaceable": noul(
        "Could this `code` be replaced by a single fast decision-model call that "
        "picks from a fixed set of options?",
        true_means="The code is deciding a label, a category, a route or a rating "
                   "from text, using keywords or a general model.",
        false_means="The code is doing real computation, I/O, formatting or "
                    "control flow unrelated to judging text."),
    "primitive": choice("If this `code` were replaced, which question shape fits?", {
        "noul":   "A yes/no judgement about the text.",
        "choice": "Pick one label from a fixed menu.",
        "score":  "Rate the text on an ordered scale.",
        "none":   "No decision-model call fits here.",
    }),
    "payoff": choice("What would be the main benefit of replacing this `code`?", {
        "accuracy":  "Keyword matching misses phrasings a model would catch.",
        "cost":      "It currently burns an expensive general model on a small decision.",
        "latency":   "It is on a hot path where a fast call would help.",
        "none":      "No real benefit.",
    }),
}


def main() -> None:
    cands = find_candidates()
    print(f"Scanned {REPO.name} and found {len(cands)} candidate spots\n")
    if not cands:
        print("No candidates found."); return

    jev = Jev()
    answers = jev.ask_many([({"code": c["snippet"]}, QUESTIONS) for c in cands])

    rows = []
    for c, a in zip(cands, answers):
        rows.append({**c,
                     "replaceable": round(a["replaceable"]["noul"], 3),
                     "primitive": a["primitive"]["choice"],
                     "payoff": a["payoff"]["choice"]})
    print(jev.report(f"audited {len(cands)} snippets"))

    strong = sorted([r for r in rows if r["replaceable"] >= 0.6 and r["primitive"] != "none"],
                    key=lambda r: -r["replaceable"])

    print(f"\n{len(strong)} spots where a Jev call would genuinely do the job:\n")
    print(f"{'p':<7}{'shape':<9}{'payoff':<11}{'found by':<22}where")
    print("-" * 104)
    for r in strong[:25]:
        print(f"{r['replaceable']:<7}{r['primitive']:<9}{r['payoff']:<11}"
              f"{r['pattern']:<22}{r['file']}:{r['line']}")
    if len(strong) > 25:
        print(f"   ... {len(strong)-25} more in the JSON")

    from collections import Counter
    print(f"\nBy shape : {dict(Counter(r['primitive'] for r in strong))}")
    print(f"By payoff: {dict(Counter(r['payoff'] for r in strong))}")

    if strong:
        top = strong[0]
        print(f"\nBest single candidate: {top['file']}:{top['line']}")
        print("-" * 70)
        print(top["snippet"][:420])
        print("-" * 70)
        print(f"Jev says: {top['primitive']} question, main win is {top['payoff']}")

    (HERE / "data" / "repo_audit.json").write_text(json.dumps(rows, indent=2))
    print(f"\nWrote data/repo_audit.json ({len(rows)} candidates, {len(strong)} strong)")


if __name__ == "__main__":
    main()
