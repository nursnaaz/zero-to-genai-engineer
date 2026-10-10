# 15 A live checker for what people say

**Advanced** | shapes used: `choice, one call per sentence`

Sort every sentence as it is spoken into decisions, action items, risks and questions. Notes build themselves during the meeting.

## Run it

```bash
cd 15_live_meeting_classifier
python3 classify_live.py
```

## Data

`data/meeting.json` - a 17-sentence engineering meeting with human labels.

## How it is tested

Asserts the per-sentence latency is faster than speech, and accuracy >= 70%.

## Result when I ran it

88% accuracy at 351ms per sentence. People speak roughly every 3.5s, so there is 10x headroom.

## Worth knowing

This use case only exists because of the latency. A frontier model cannot keep up with a talking human.

← [all use cases](../README.md)
