# 13 Search that knows what you mean

**Intermediate** | shapes used: `choice`

Ctrl-F that works when your words never appear on the page. Split into paragraphs, let Jev pick the match.

## Run it

```bash
cd 13_semantic_find_in_page
python3 semantic_find.py
```

## Data

`data/page.json` - a 13-paragraph technical page.

## How it is tested

7 queries, 6 of which share NO keywords with their target, so plain find-in-page returns nothing.

## Result when I ran it

6/7 landed on the paragraph a human wanted, 469ms average.

## Worth knowing

The one miss ('how do I stop it making things up' -> RAG intro instead of the faithfulness paragraph) is arguably defensible, and came in at the lowest confidence of the set.

← [all use cases](../README.md)
