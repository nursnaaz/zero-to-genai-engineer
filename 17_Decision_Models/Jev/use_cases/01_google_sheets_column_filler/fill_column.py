"""
Use case 01 - Put Jev in a spreadsheet column.

You type a new column header (like Category) and a list of allowed options.
Jev fills every row. Because Jev can only pick from your list, it can never
invent a category you did not ask for -- that is the whole point.

Run:  python3 fill_column.py
"""
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _shared.jev_client import Jev, choice            # noqa: E402

HERE = Path(__file__).parent

# The allowed options. "Other" is the way out, so Jev never forces a bad pick.
CATEGORIES = {
    "Groceries":  "Supermarkets and food shopping to cook at home.",
    "Software":   "SaaS subscriptions, developer tools and cloud bills.",
    "Travel":     "Flights, hotels, taxis and transport.",
    "Eating out": "Restaurants, cafes, food delivery and takeaway.",
    "Other":      "Anything that does not clearly fit the categories above.",
}


def fill(rows: list[dict], header: str = "Category") -> list[dict]:
    """Ask Jev one choice question per row, in parallel."""
    jev = Jev()
    questions = {
        header.lower(): choice(
            f"Which category does this expense belong to? Use `merchant` and `note`.",
            CATEGORIES,
        )
    }
    answers = jev.ask_many([(row, questions) for row in rows])

    for row, ans in zip(rows, answers):
        a = ans[header.lower()]
        row[header] = a["choice"]
        row["confidence"] = round(a["confidence"], 3)
    print(jev.report(f"filled {len(rows)} rows"))
    return rows


def main() -> None:
    rows = list(csv.DictReader(open(HERE / "data" / "expenses.csv")))
    filled = fill(rows)

    out = HERE / "data" / "expenses_categorised.csv"
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(filled[0].keys()))
        w.writeheader()
        w.writerows(filled)

    print(f"\n{'merchant':<24}{'category':<12}conf")
    print("-" * 46)
    for r in filled:
        print(f"{r['merchant'][:23]:<24}{r['Category']:<12}{r['confidence']}")

    # Every value must come from our list -- this is the guarantee Jev gives us.
    assert all(r["Category"] in CATEGORIES for r in filled), "Jev invented a category!"
    print(f"\nAll {len(filled)} values are inside the allowed list.")
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
