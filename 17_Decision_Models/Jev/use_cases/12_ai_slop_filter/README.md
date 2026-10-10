# 12 Build Chrome extensions

**Intermediate** | shapes used: `noul`

One question per post as the feed loads; fold the post away when Jev is over 80% sure it is AI slop.

## Run it

```bash
cd 12_ai_slop_filter
python3 filter_feed.py
```

## Data

`data/posts.json` - 14 feed posts, half genuine engineering observations, half engagement bait.

## How it is tested

Asserts zero genuine posts were hidden (the error users hate) and at least 70% of slop caught.

## Result when I ran it

6/7 slop folded, 0 genuine posts hidden, 443ms per post. The miss scored 0.79, just under the 0.80 gate.

## Worth knowing

Ships the real extension: manifest v3, MutationObserver for infinite feeds, per-post caching, and a 'Show anyway' button.

## Chrome extension

`extension/` is a real manifest v3 extension. Load it with chrome://extensions > Developer mode > Load unpacked, then open the options page and paste your Jev key.

← [all use cases](../README.md)
