# 10 Let Jev pick the right model

**Intermediate** | shapes used: `score + noul`

Classify how hard each request is, then hand it to the cheapest model that can do the job.

## Run it

```bash
cd 10_model_router
python3 route_models.py
```

## Data

`data/tasks.json` - 16 prompts a developer actually types, labelled trivial / simple / hard.

## How it is tested

Asserts no hard task is sent to the cheapest tier (the expensive mistake).

## Result when I ran it

57% relative cost saving across 16 prompts, 449ms routing overhead, zero hard tasks under-routed.

## Worth knowing

Tier prices are illustrative placeholders; swap your real numbers before quoting the saving.

← [all use cases](../README.md)
