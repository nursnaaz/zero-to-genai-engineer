# 11 Put Jev in front of your AI agents

**Intermediate** | shapes used: `3 x noul in one call`

Screen every email with three cheap questions so only the ones needing a reply reach your expensive agent.

## Run it

```bash
cd 11_email_prefilter
python3 prefilter.py
```

## Data

`data/inbox.json` - 19 emails: genuine replies, brand deals, scams and noise.

## How it is tested

Two assertions that matter: zero scams reach the agent, zero genuine replies get dropped.

## Result when I ran it

6/19 emails reach the agent (32%). Zero scams through, zero real replies lost.

## Worth knowing

A gold label was WRONG here and Jev was right: 'Works for me, see you Thursday' scored 0.43 on needs-reply. Relabelled, and a short genuine question added to keep the test honest - it scored 0.94.

← [all use cases](../README.md)
