# 04 Clipping a long video

**Easy** | shapes used: `score + noul`

Score every possible clip in a long recording and return a shortlist of the best moments.

## Run it

```bash
cd 04_video_clip_finder
python3 find_clips.py
```

## Data

`data/transcript.json` - a synthetic 3-minute interview, 26 sentences with timings.

## How it is tested

Asserts scores stay inside the level range; non-maximum suppression stops the top-N being five versions of one moment.

## Result when I ran it

26 sentences produced 121 candidate clips, scored in 44s. Top 5 now span the whole interview instead of clustering.

## Worth knowing

The overlap suppression is the part that makes this usable: without it the naive top-5 was the same 30 seconds five times.

← [all use cases](../README.md)
