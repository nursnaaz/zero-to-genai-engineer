"""
Use case 14 - Search your images by what is IN them.

Each image has a one-line caption (your saved prompt, or one written by a
cheap vision model). Jev picks which captions match what you typed. Typing
"claude" finds images about Claude, not images with claude in the filename.

Run:  python3 search_images.py
"""
import json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _shared.jev_client import Jev, noul              # noqa: E402

HERE = Path(__file__).parent
MATCH_AT = 0.55

# (query, filenames a human would expect back)
QUERIES = [
    ("diagrams explaining how models work",
     {"rag_architecture.png", "attention_heatmap.png", "lora_matrices.png"}),
    ("something I could use on a slide about cost or speed",
     {"jev_latency_chart.png"}),
    ("photos with people in them",
     {"team_offsite_2026.jpg", "conference_stage.jpg", "family_beach.jpg"}),
    ("screenshots of developer tools",
     {"claude_code_terminal.png", "aws_console_cdk.png", "kubernetes_dashboard.png"}),
]


def main() -> None:
    images = json.loads((HERE / "data" / "images.json").read_text())
    jev = Jev()

    print(f"Index: {len(images)} images with captions\n")
    total_p = total_r = 0.0

    for query, expected in QUERIES:
        # one cheap noul per image -- all in parallel
        answers = jev.ask_many([
            ({"caption": im["caption"], "search": query},
             {"match": noul("Does the image described by `caption` match what the "
                            "user is looking for in `search`?")})
            for im in images])

        hits = [(im, a["match"]["noul"]) for im, a in zip(images, answers)
                if a["match"]["noul"] >= MATCH_AT]
        hits.sort(key=lambda x: -x[1])
        got = {im["filename"] for im, _ in hits}

        tp = len(got & expected)
        precision = tp / len(got) if got else 0.0
        recall = tp / len(expected)
        total_p += precision; total_r += recall

        print(f'  "{query}"')
        for im, p in hits:
            mark = "ok " if im["filename"] in expected else "?? "
            print(f"      {mark}{p:.2f}  {im['filename']}")
        missed = expected - got
        for m in missed:
            print(f"      MISS      {m}")
        print(f"      precision {precision:.2f}  recall {recall:.2f}\n")

    n = len(QUERIES)
    print(f"Mean precision {total_p/n:.2f}, mean recall {total_r/n:.2f}")
    print(jev.report("image search"))
    assert total_r / n >= 0.6, "recall too low to be a useful search box"


if __name__ == "__main__":
    main()
