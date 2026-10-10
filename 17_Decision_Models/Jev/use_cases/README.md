# The 19 Jev use cases, built and tested

Every use case from `Jev Use Cases Guide.pdf`, implemented as runnable code with
its own data and its own assertions. All 19 pass against the live API.

```bash
python3 run_all.py            # runs all 19 and reports pass/fail
cd 08_validate_jev_accuracy && python3 validate.py    # or run one
```

**Setup:** the key is read from `../.env` (`JEV_KEY`). No install needed beyond
`requests`. The guide routes through OpenRouter; these call the TypeSafe API
directly, which is one fewer moving part and the same model.

---

## What Jev is, in one paragraph

Jev does not write sentences. It picks, in three shapes only: **noul** (true/false,
returns a probability), **choice** (one option from your menu), **score** (a position
on an ordered scale). Because it can only answer from the options you supply, it
cannot invent a category that does not exist. That constraint is the product.

---

## Results

| # | Use case | Tier | Shapes | Headline result |
|---|---|---|---|---|
| 01 | [Google Sheets column filler](01_google_sheets_column_filler/) | Easy | choice | 30/30 rows, all inside the allowed set |
| 02 | [Customer inquiry triage](02_customer_inquiry_triage/) | Easy | choice | 55/60 automated at **98.2%**, 5 to humans |
| 03 | [Competitor ad tagger](03_competitor_ad_tagger/) | Easy | 3x choice | 18 ads x 3 questions in 7.5s |
| 04 | [Video clip finder](04_video_clip_finder/) | Easy | score + noul | 121 candidates scored, top 5 non-overlapping |
| 05 | [Customer churn profiler](05_customer_churn_profiler/) | Easy | score + choice | 40 accounts, all 3 cancellers escalated |
| 06 | [Internal backlink builder](06_internal_backlink_builder/) | Easy | choice | 11 links, zero broken, zero self-links |
| 07 | [Find buyers in comments](07_find_buyers_in_comments/) | Easy | choice + noul | 11 buyers surfaced from 40, 71% recall |
| 08 | [**Validate Jev's accuracy**](08_validate_jev_accuracy/) | Easy | measured | **93.3% held out; 100% above 0.9 confidence** |
| 09 | [Skill picker](09_skill_picker/) | Inter | choice | **13/14 on this course's real skills** |
| 10 | [Model router](10_model_router/) | Inter | score + noul | **57% cost saving**, 0 hard tasks under-routed |
| 11 | [Email prefilter](11_email_prefilter/) | Inter | 3x noul | 32% reach the agent, 0 scams through |
| 12 | [AI slop filter](12_ai_slop_filter/) | Inter | noul | 6/7 slop folded, **0 genuine posts hidden** |
| 13 | [Semantic find-in-page](13_semantic_find_in_page/) | Inter | choice | 6/7, where plain Ctrl-F finds nothing |
| 14 | [Image search by caption](14_image_search_by_caption/) | Inter | noul | precision 0.94, recall 1.00 |
| 15 | [Live meeting classifier](15_live_meeting_classifier/) | Adv | choice | 88% at **351ms/sentence, 10x speech headroom** |
| 16 | [Zero-LLM chatbot](16_zero_llm_chatbot/) | Adv | choice x2 | 8/8, **zero prose tokens generated** |
| 17 | [Smart icon picker](17_smart_icon_picker/) | Adv | choice | 13/14 against a 40-icon menu |
| 18 | [Self-assembling page](18_self_assembling_page/) | Adv | 9x score | 4 of 9 sections chosen in 401ms |
| 19 | [Find your own use cases](19_find_your_own_use_cases/) | Adv | noul + choice | **385 scanned, 6 real hits in this repo** |

Plus two real Chrome extensions (03, 12) and a Google Apps Script add-on (01).

---

## The four habits from page 3, and where to see each one working

| Habit | Where it is demonstrated |
|---|---|
| **Give Jev a way out** | A `None` option in 01, 06, 09, 16, 17 |
| **Send the unsure ones to a person** | The confidence gate in 02, measured properly in 08 |
| **Check before you trust it** | 08 is nothing but this |
| **Jev decides, Claude writes** | 11: Jev screens 19 emails, only 6 reach the writing agent |

---

## Three findings worth teaching

**Tuning on the wrong half proves nothing.** In use case 08, rewriting the category
descriptions lifted the tune half from 96.7% to 100%. The held-out half did not move:
93.3% before, 93.3% after. That is overfitting caught live, and it is the reason the
method splits the data at all.

**Confidence is a usable control, not decoration.** Still in 08: above 0.9 confidence
Jev was right 27 out of 27. Between 0.7 and 0.9 it was right half the time. Set the
gate at 0.8 and you automate 90% of traffic with zero errors on this data.

**Sometimes the human label is the wrong one.** In use case 11, Jev gave 0.43 to
"Works for me, see you Thursday at 10" on *does this need a reply*. My label said it
did. Jev was right: a closing confirmation needs no reply. The label was corrected and
a genuinely open question added to keep the test honest, which scored 0.94. Confidence
near the middle is often the model telling you your taxonomy is fuzzy.

---

## Cost and speed actually observed

Around 900 Jev calls across all 19 use cases, averaging **370-480ms** each, roughly
**450k input / 75k output tokens** in total. Every use case prints its own
`calls / seconds / tokens` line, so the numbers above are reproducible rather than
quoted from the guide.

← [S17 Decision Models](../../)
