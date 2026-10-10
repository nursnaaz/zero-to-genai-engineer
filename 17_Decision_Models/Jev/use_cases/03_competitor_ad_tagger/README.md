# 03 Analyze your competitor ads

**Easy** | shapes used: `3 x choice in ONE call (speculative fan-out)`

Build a swipe file of competitor ads, each tagged with format, call to action and funnel stage.

## Run it

```bash
cd 03_competitor_ad_tagger
python3 tag_ads.py
```

## Data

`data/ads.json` - 18 synthetic SaaS ads across 3 brands.

## How it is tested

Asserts every funnel stage is one of the three allowed values; prints the market summary.

## Result when I ran it

18 ads x 3 questions in 18 calls, 7.5s. Market summary showed educational/demo formats dominating.

## Worth knowing

Also ships a real Chrome extension for the Meta Ad Library with a CSV export button.

## Chrome extension

`extension/` is a real manifest v3 extension. Load it with chrome://extensions > Developer mode > Load unpacked, then open the options page and paste your Jev key.

← [all use cases](../README.md)
