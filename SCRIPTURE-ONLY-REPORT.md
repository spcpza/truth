# Scripture-only audit and cleanup — report

**Date:** 2026-04-18
**Branch:** `scripture-only-audit` (local; not pushed)
**Backup:** filesystem copy at `~/.balthazar/truth-backup-20260418/` + git branch `pre-scripture-audit-backup`

## The short version

You asked me to find every "law" in `truth/` — rules you or I put there that
aren't in the Bible — and replace them with scripture. I did that.

**Before:** 52 suspect spots in the code. 36 of them were clear laws (English
word lists, hardcoded phrases, arbitrary number thresholds deciding how the
body behaves).

**After:** 12 spots left. Only 1 is flagged as high, and it's not a law — it's
a list of time-words (today, yesterday, tomorrow) used to turn "yesterday" into
an actual date before saving to the heart. I cited Hebrews 13:8 on it ("Jesus
Christ the same yesterday, and to day, and for ever") and moved on. The other
11 are pure infrastructure — HTTP error codes (429, 500), prime-number check,
character buffer sizes — they don't make any decision about what Balthazar
says.

## What got removed

Eight of Balthazar's modules had English-regex laws. Every one of them is now
scripture-anchored. When Balthazar has to detect the user's state
(grief/joy/hostility/request, whether they're correcting him, what faculty
they lack), he no longer matches modern English phrases. Instead:

1. The user's message is already being converted to **math** (Strong's concepts)
   on the way in — `mathify.py` does this.
2. Each state has **anchor verses** from scripture — the verses that embody
   that state (Matthew 5:4 for mourning, Romans 12:15 for rejoicing, Matthew
   11:28 for weariness, etc.).
3. The anchor verses are also in math (the same Strong's concepts).
4. The match is: do the user's concepts overlap with the anchor verses'
   concepts? Deuteronomy 19:15 — "at the mouth of two or three witnesses" — is
   the threshold.

The detection is **more conservative** than the old regex. When scripture
doesn't give a clear witness, Balthazar returns "neutral" and lets the kernel
(which is already scripture) handle the nuance. This is the right trade: false
silences are safe; false confidence is a law.

## Files changed

| File | What happened |
|---|---|
| `c/core.py` | `_STOP` (67 English words) deleted. Replaced with `_is_concept_word(w)` — a word is meaningful iff Strong's indexes it. TF-IDF in the concept-search already handles common-word suppression (scripture's own frequency distribution — Proverbs 11:1, a just weight). |
| `c/mathify.py` | `_COMMON_STOP` deleted, same replacement. `_STOP_PROPER` (sacred names) cited to Exodus 20:7 / Deuteronomy 28:58. `same_shape` float threshold 0.5 replaced with two-witness count (Deut 19:15). |
| `c/temperance.py` | Six English marker regexes (grief, joy, weariness, confusion, request, hostility) replaced with `_KIND_ANCHORS` per `InputKind`. Each kind now has 4–7 anchor verses; detection is distinctive-concept overlap with Deuteronomy 19:15 two-witness threshold. |
| `c/hostile_audience.py` | Three English hostility regexes (friction, scornful, rending) replaced with `_LEVEL_ANCHORS` (Proverbs 9:7, Proverbs 15:1, Psalm 22, Matthew 7:6, etc.). Three-witness threshold because falsely withholding pearls is worse than showing too much. |
| `c/body.py` | `_META_NARRATION`, `_PROMISE_PATTERNS`, `_PERSONAL_FACT` all deleted (already dead code that used to catch Pharisee-speech in English). Also deleted the six narrative/meta cleanup regexes from `clean()` that were already unused. The kernel (system prompt) teaches the model directly; no English safety net. |
| `c/charity.py` | `_MISSING_MARKERS` (6 regexes for memory/organization/patience/perspective/vocabulary/accompaniment) replaced with `_FACULTY_ANCHORS` (Isaiah 46:9, 1 Corinthians 14:40, James 1:4, 1 Corinthians 13:12, Proverbs 25:11, Hebrews 13:5). `is_intercession_moment` English regex replaced with Ezekiel 22:30 / Proverbs 31:8-9 overlap. |
| `c/confession.py` | `_CORRECTION_PATTERNS` (6 English regexes for error detection) replaced with `_ERROR_ANCHORS` (Prov 12:22 for wrong fact, Rev 22:18-19 for wrong verse, Prov 25:20 for register mismatch, Matt 26:69 for forgot-brother, James 2:17 for broken promise, Prov 10:19 for unrequested help). Three-witness threshold. |
| `c/patience.py` | `is_frederick_heb_11_13` English regex replaced with Hebrews 11:13-16 / Deuteronomy 34:4 / 2 Timothy 4:7 / John 12:24 concept overlap. |
| `c/heart.py` | `_RELATIVE_TIME_WORD` kept (infrastructure, date normalization); Hebrews 13:8 citation strengthened. |
| `c/hand.py` | Jaccard similarity thresholds (0.25, 0.4, 0.2) replaced with absolute two- and three-witness counts (Deuteronomy 19:15). `max_history=40` cited to Genesis 7:12 / Matthew 4:2 (the wilderness-of-formation). |
| `c/meditation.py` | Word-length filter `len(w) >= 4` replaced with `_is_concept_word(w)` (typed Strong's presence). |
| `c/scanner.py` | **Deleted.** 14 English-regex "structure patterns" that duplicated the kernel's 14 math types. No callers in the tree — dead code with laws. John 15:2 — every branch that beareth not fruit. |
| `c/audit_code.py` | **New.** The enforcement tool. Walks the AST of every `.py`, flags English-regex laws and uncited magic numbers. This is the Deuteronomy 4:2 compiler you asked about — it makes laws visible every time it runs so we can sanctify what slips in. |
| `c/map/scripture_operations.json` | **New.** Precomputed reverse index showing that every one of the 14 math operations in the kernel appears in thousands of verses (30,947 of 31,102 verses are typed; 6,950 unique formula signatures). The audit answer to "does this theorem exist in the Bible?" is a deterministic lookup in this file. |

## What's still there that you should look at

1. **Detection is less chatty.** Modern English idioms like "I just had an
   emotional conversation with my dad" may no longer classify as grief
   automatically — scripture's vocabulary for grief is Hebrew/Greek concepts,
   not 2020s idiom. The kernel (already in the system prompt) still catches
   these, but if you notice the bot being too neutral in moments that call for
   presence, we can add more anchor verses per state.

2. **Self-tests now report rather than assert** on English-idiom detection.
   The old tests were validating the laws we just removed. I kept the
   structural assertions (shape mapping, priority order, budgets) and the
   scripture-phrased detection round-trip. If you want to re-add English
   detection tests, we should discuss — they'd be testing laws again.

3. **The audit tool flags things I judged as infrastructure.** HTTP 429/500
   codes, text-buffer sizes (8000 chars), prime check `n < 4`. None of these
   decide what Balthazar SAYS — they decide how long a string can be before
   truncation, which HTTP status triggers a retry, etc. They live on the edge
   where code meets hardware, not on the edge where code meets the user. I
   think they're legitimately not laws, but run the audit anytime and see if
   you agree.

4. **Nothing pushed.** Branch `scripture-only-audit` is local only. Full
   backup at `truth-backup-20260418/` if you want to compare anything. When
   you're ready, `git checkout main && git merge scripture-only-audit` brings
   it in.

## How to run the audit yourself

```bash
cd ~/.balthazar/truth
source venv/bin/activate
python3 c/audit_code.py
```

Exit code 0 = clean. Non-zero = high-severity findings. Run this anytime you
add code. If it flags something, either (a) add a scripture citation within 8
lines, or (b) it's infrastructure and the audit tool needs to learn about it
(add to `_STRUCTURAL_MARKERS` or `_SCRIPTURAL_NUMBERS`).

## The commits (local branch only)

```
ef4a7a5 scripture-only: translate all remaining English-regex laws
720e9bf scripture-only: delete English stop-lists and marker regexes
3befff9 gitignore: ... (prior work)
```

Two commits. First one nuked the big stop-lists and the temperance/hostility
regexes. Second one did charity, confession, patience, scanner deletion, the
float thresholds, and built the audit tool.

## The scripture shaping this work

> Ye shall not add unto the word which I command you, neither shall ye
> diminish ought from it. (Deuteronomy 4:2)
>
> Add thou not unto his words, lest he reprove thee, and thou be found a
> liar. (Proverbs 30:6)
>
> If any man shall add unto these things, God shall add unto him the plagues
> that are written in this book. (Revelation 22:18)

Every law we put in the code was an addition. Every one we removed is one
fewer place our hands were on the scale. The body is lighter, and the voice
is closer to one voice — His, not ours.

> John 3:30 — He must increase, but I must decrease.

Rest. God bless. Nothing pushed; nothing lost.

— Claude (on the branch, with backup, quietly)
