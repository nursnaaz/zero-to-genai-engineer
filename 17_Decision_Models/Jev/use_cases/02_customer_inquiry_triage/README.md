# 02 Triage customer inquiries

**Easy** | shapes used: `choice + confidence gate`

Tag each inbound message and route it. Anything below the confidence threshold goes to a human instead of an automation.

## Run it

```bash
cd 02_customer_inquiry_triage
python3 triage.py
```

## Data

`data/tickets_labelled.json` - 60 support messages with human gold labels (billing / bug / how-to / other).

## How it is tested

Measures accuracy on the automated slice separately from overall accuracy, and prints every message that was automated but wrong.

## Result when I ran it

At a 0.60 threshold: 55/60 automated at 98.2% accuracy, 5 routed to a human, 90.0% overall.

## Worth knowing

Threshold is one constant at the top of the file; pass a different one on the command line.

← [all use cases](../README.md)
