# 06 Build backlinks inside your site or second brain

**Easy** | shapes used: `choice (+ a None escape)`

For each page, pick which other page it should link to. The menu is the rest of your site, so a broken link is structurally impossible.

## Run it

```bash
cd 06_internal_backlink_builder
python3 build_links.py
```

## Data

`data/pages.json` - 12 interlinked blog pages on RAG, agents and fine-tuning.

## How it is tested

Asserts every suggested target is a real page and nothing links to itself.

## Result when I ran it

11 link suggestions from 12 pages in 5.8s, 1 page correctly got no suggestion.

## Worth knowing

Works the same on an Obsidian vault: swap the page list for your notes.

← [all use cases](../README.md)
