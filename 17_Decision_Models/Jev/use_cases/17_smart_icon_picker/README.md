# 17 Smart features for any app

**Advanced** | shapes used: `choice (+ None)`

User types a habit in their own words, Jev picks the icon from your set of 40.

## Run it

```bash
cd 17_smart_icon_picker
python3 pick_icon.py
```

## Data

`data/icons.json` - 40 habit-tracker icon names.

## How it is tested

14 habits phrased naturally; asserts no invented icon and >=80% acceptable picks.

## Result when I ran it

13/14 acceptable (93%), 418ms per pick against a 40-option menu.

## Worth knowing

The None option matters: 'reorganise my sock drawer by colour' has no good icon, and a wrong icon is worse than a default.

← [all use cases](../README.md)
