# 08 Verify Jev's results

**Easy** | shapes used: `choice, measured`

The one that makes the other eighteen defensible. Split labelled data, tune on one half, report only on the half you never looked at, and show accuracy per confidence band.

## Run it

```bash
cd 08_validate_jev_accuracy
python3 validate.py
```

## Data

Reuses the 60 labelled tickets from use case 02.

## How it is tested

This IS the test. Asserts held-out accuracy stays above the bar you would ship at.

## Result when I ran it

Tuning lifted the TUNE half 96.7% -> 100%, but held-out stayed 93.3%. Above 0.9 confidence: 100% accurate on 27/30. At a 0.8 threshold you automate 90% of traffic with zero errors.

## Worth knowing

The flat held-out number next to the improved tune number is a live demonstration of overfitting. Keep it in the lesson.

← [all use cases](../README.md)
