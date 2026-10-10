"""
Use case 13 - Ctrl-F that understands what you mean.

Split the page into paragraphs, make them the menu, ask Jev which one matches
the query. Works when your words never appear in the text, which is exactly
where normal find-in-page gives up.

Run:  python3 semantic_find.py
"""
import json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _shared.jev_client import Jev, choice            # noqa: E402

HERE = Path(__file__).parent

# (query, index of the paragraph a human would want, does the wording overlap?)
QUERIES = [
    ("why is my answer cut in half",                 2,  False),
    ("stuff about error codes and SKUs",             6,  False),
    ("the bit where it ignores the middle",          9,  False),
    ("how do I stop it making things up",           10,  False),
    ("what makes my bill expensive",                12,  False),
    ("merging two ranked lists",                     7,  True),
    ("someone hiding instructions in a document",   11,  False),
]


def main() -> None:
    paras = json.loads((HERE / "data" / "page.json").read_text())
    menu = {str(p["i"]): p["text"][:200] for p in paras}
    jev = Jev()

    answers = jev.ask_many([
        ({"query": q}, {"paragraph": choice(
            "Which paragraph of the page best answers `query`?", menu)})
        for q, _, _ in QUERIES])

    hits = 0
    print(f"{'query':<42}{'picked':<8}{'want':<7}{'conf':<7}keyword overlap?")
    print("-" * 92)
    for (q, want, overlap), ans in zip(QUERIES, answers):
        a = ans["paragraph"]
        got = int(a["choice"])
        ok = got == want
        hits += ok
        print(f"{q[:40]:<42}{got:<8}{want:<7}{a['confidence']:.2f}   "
              f"{'yes' if overlap else 'NO - plain Ctrl-F fails here':<30}{'' if ok else '  <- miss'}")

    print(f"\n{hits}/{len(QUERIES)} landed on the paragraph a human wanted")
    no_overlap = [(q,w) for q,w,o in QUERIES if not o]
    print(f"{len(no_overlap)} of these queries share no keywords with the target "
          f"paragraph, so a normal find-in-page returns nothing at all.")
    print(jev.report("semantic find"))

    assert hits >= len(QUERIES) - 1, f"too many misses: {hits}/{len(QUERIES)}"


if __name__ == "__main__":
    main()
