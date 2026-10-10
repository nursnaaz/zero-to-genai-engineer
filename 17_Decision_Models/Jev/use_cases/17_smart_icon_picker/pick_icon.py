"""
Use case 17 - Smart features for an ordinary app.

Someone types a new habit, Jev picks the icon from your set of 40. Before
models like this you needed either a costly LLM call or keyword matching that
missed anything phrased unusually. Note the None option: when nothing fits we
want the default icon, not a wrong one.

Run:  python3 pick_icon.py
"""
import json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _shared.jev_client import Jev, choice            # noqa: E402

HERE = Path(__file__).parent

# (what the user typed, the icon we would accept)
HABITS = [
    ("drink more water", {"water"}),
    ("go for a run before work", {"run"}),
    ("read 20 pages", {"book"}),
    ("stop smoking", {"no-smoking"}),
    ("call mum on Sundays", {"call", "family"}),
    ("practise guitar", {"guitar"}),
    ("8 hours sleep", {"bed", "moon"}),
    ("learn Arabic", {"language", "study"}),
    ("track my spending", {"money", "budget"}),
    ("water the plants", {"plant", "water"}),
    ("walk the dog", {"dog", "walk"}),
    ("floss", {"tooth"}),
    ("ship one commit a day", {"code", "write"}),
    ("reorganise my sock drawer by colour", {"clean", "none"}),
]


def main() -> None:
    icons = json.loads((HERE / "data" / "icons.json").read_text())
    menu = {i: i.replace("-", " ") for i in icons}
    menu["none"] = "Nothing in the set fits; use the default icon."
    print(f"{len(icons)} icons in the set, plus a None escape hatch\n")

    jev = Jev()
    answers = jev.ask_many([
        ({"habit": h}, {"icon": choice("Which icon best represents `habit`?", menu)})
        for h, _ in HABITS])

    hits = 0
    print(f"{'habit typed by the user':<40}{'icon':<14}{'conf':<7}ok")
    print("-" * 70)
    for (habit, accept), ans in zip(HABITS, answers):
        a = ans["icon"]
        ok = a["choice"] in accept
        hits += ok
        print(f"{habit:<40}{a['choice']:<14}{a['confidence']:.2f}   {'y' if ok else 'NO'}")

    print(f"\n{hits}/{len(HABITS)} acceptable = {100*hits/len(HABITS):.0f}%")
    print(jev.report(f"{len(HABITS)} habits against {len(icons)} icons"))
    assert all(ans["icon"]["choice"] in menu for ans in answers), "invented an icon"
    assert hits >= len(HABITS) * 0.8, "icon picking not reliable enough to ship"


if __name__ == "__main__":
    main()
