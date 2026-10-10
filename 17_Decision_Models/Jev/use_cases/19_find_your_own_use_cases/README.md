# 19 Find your own Jev use cases

**Advanced** | shapes used: `noul + 2 x choice`

Scan a real codebase for Jev-shaped work: keyword matching standing in for understanding, elif ladders on text, and general models used to produce one label.

## Run it

```bash
cd 19_find_your_own_use_cases
python3 scan_repo.py
```

## Data

THIS repository. No synthetic data at all.

## How it is tested

Scans every .py file outside the skip list, then has Jev audit each candidate snippet.

## Result when I ran it

385 candidates found, 6 genuinely replaceable. Top hit: `11_LangGraph/multi_agent_orchestrator/graph.py:550` routes on `if "agent" in q` keyword matching.

## Worth knowing

That top hit is real and worth fixing: the current code breaks on 'show me the people working on this' because the word 'agent' never appears.

← [all use cases](../README.md)
