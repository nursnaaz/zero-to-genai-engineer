# 07 Find buyers in your comments

**Easy** | shapes used: `choice + noul`

Tag every comment so the people ready to buy float to the top of a work queue.

## Run it

```bash
cd 07_find_buyers_in_comments
python3 find_buyers.py
```

## Data

`data/comments.json` - 40 synthetic social comments with hand hints.

## How it is tested

Measures recall against the hand-marked buyers and asserts it stays above 60%.

## Result when I ran it

11 ready-to-buy comments surfaced from 40 (28% of the pile), 71% recall against the hand marks.

## Worth knowing

In production you would feed this from Apify; the saved export keeps it runnable offline.

← [all use cases](../README.md)
