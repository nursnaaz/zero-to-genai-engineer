"""
Use case 06 - Build internal links across a site or second brain.

For every page, ask Jev which OTHER page it should link to. The menu is the
rest of your site, so Jev can never suggest a page that does not exist --
that is the structural guarantee a text model cannot give you.

Run:  python3 build_links.py
"""
import json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _shared.jev_client import Jev, choice, noul      # noqa: E402

HERE = Path(__file__).parent
MIN_CONF = 0.35          # below this we do not suggest a link at all


def main() -> None:
    pages = json.loads((HERE / "data" / "pages.json").read_text())
    jev = Jev()

    requests_ = []
    for page in pages:
        others = {p["url"]: f"{p['title']} - {p['summary']}"
                  for p in pages if p["url"] != page["url"]}
        others["none"] = "No other page is a natural link target from here."
        requests_.append((
            {"page_title": page["title"], "page_summary": page["summary"]},
            {"target": choice(
                "Which other page would a reader of this page most naturally want next?",
                others),
             "same_topic": noul(
                "Is this page about retrieval or search, as opposed to training or cost?")},
        ))

    answers = jev.ask_many(requests_)
    print(jev.report(f"linked {len(pages)} pages"))

    links = []
    for page, ans in zip(pages, answers):
        t = ans["target"]
        if t["choice"] == "none" or t["confidence"] < MIN_CONF:
            continue
        links.append({"from": page["url"], "to": t["choice"],
                      "confidence": round(t["confidence"], 3),
                      "from_title": page["title"]})

    links.sort(key=lambda l: -l["confidence"])
    print(f"\n{len(links)} link suggestions, best first:\n")
    print(f"{'from':<22}{'to':<22}conf")
    print("-" * 52)
    for l in links:
        print(f"{l['from']:<22}{l['to']:<22}{l['confidence']}")

    urls = {p["url"] for p in pages}
    assert all(l["to"] in urls for l in links), "Jev suggested a page that does not exist"
    assert all(l["to"] != l["from"] for l in links), "page linked to itself"
    print(f"\nAll targets are real pages, no self-links. "
          f"{len(pages)-len(links)} pages got no suggestion (below {MIN_CONF} or 'none').")
    (HERE / "data" / "link_suggestions.json").write_text(json.dumps(links, indent=2))


if __name__ == "__main__":
    main()
