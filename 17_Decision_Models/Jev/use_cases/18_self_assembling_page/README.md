# 18 Web pages that build themselves

**Advanced** | shapes used: `9 x score in ONE call`

Score every prebuilt section for this visitor and assemble the page from the top four. Jev chooses the parts, it does not write them.

## Run it

```bash
cd 18_self_assembling_page
python3 assemble.py
```

## Data

`data/visitors.json` - 6 visitor profiles (referrer, search query, returning, logged in, plan).

## How it is tested

Prints the page each visitor is served plus the section scores behind it.

## Result when I ran it

401ms to choose 4 of 9 sections, inside a normal page-load budget. A visitor searching 'rag studio pricing' got pricing first at 3.0.

## Worth knowing

Because Jev only picks prebuilt parts, the page renders at normal speed - nothing is generated.

← [all use cases](../README.md)
