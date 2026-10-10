# 05 Score and profile your customer base

**Easy** | shapes used: `score + choice`

Score churn risk from the account facts you already have, then bucket into Healthy / Needs attention / At risk.

## Run it

```bash
cd 05_customer_churn_profiler
python3 profile_customers.py
```

## Data

`data/customers.csv` - 40 synthetic accounts (tenure, plan, last login, cancellation started, open tickets, seats).

## How it is tested

Asserts no account that has already started cancelling is labelled Healthy.

## Result when I ran it

40 accounts profiled in 15s. 9 At risk, 17 Needs attention, 14 Healthy; all 3 actively-cancelling accounts correctly escalated.

## Worth knowing

Bucket thresholds live in our code, not the model. Jev supplies the number, policy stays yours.

← [all use cases](../README.md)
