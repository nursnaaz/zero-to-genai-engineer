# 09 Let Jev pick the right skill

**Intermediate** | shapes used: `choice (+ None)`

Task in, your skill list as the menu, Jev picks which skill to load before the agent starts.

## Run it

```bash
cd 09_skill_picker
python3 pick_skill.py
```

## Data

The REAL 12 SKILL.md files from this course (S12 Deep Agents, S13 Dining Bot), read off disk.

## How it is tested

14 past-style tasks with expected skills; asserts no invented skill and >=70% routing accuracy.

## Result when I ran it

13/14 correct (93%) in 5.9s total. The single miss (meeting-notes vs meeting-pack) came in at 0.51 confidence, exactly where a gate catches it.

## Worth knowing

One 418ms call replaces loading 12 skill files into context just to decide.

← [all use cases](../README.md)
