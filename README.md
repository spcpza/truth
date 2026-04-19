# truth — the zero build

Three files. No code. No framework. No opinions.

```
kjv.json       31,102 verses — the WORD in English (King James)
strongs.json   5 indexes — the WORD's Hebrew and Greek roots (Strong's)
```

That is the whole package.

## What this is

The WORD, machine-readable, for any agent that wants to read it.

- `kjv.json` maps every reference (`"John 1:1"`) to its KJV text.
- `strongs.json` gives five ways to walk the original languages:
  - `ci`    — concept → verses where it appears
  - `sm`    — Strong's number → original word + transliteration
  - `s2e`   — Strong's → English words
  - `e2s`   — English → Strong's numbers
  - `roots` — Strong's → etymological root

Point any model at these files. Let it read. The reader meets what the
WORD says on its own terms, with no intermediary.

## What this is not

Not a theological framework. Not a reasoning engine. Not a proof of
anything. Earlier versions of this repo carried a `kernel.md` with
theorems, constraints, virtues — all deleted on 2026-04-19. *Ye shall
not add unto the word which I command you* (Deut 4:2). What remains is
only what was given.

There is no Python code in this repo. The caller that uses these files
(to ground a Telegram bot named Balthazar) is a separate thing.

## How to use

```python
import json
kjv     = json.load(open("kjv.json"))
strongs = json.load(open("strongs.json"))

# any verse
kjv["John 1:1"]
# → "In the beginning was the Word, and the Word was with God..."

# every verse that uses ἀγάπη (love)
strongs["ci"]["G25"]
# → ["Matthew 24:12", "Luke 11:42", ...]

# what's the original word at G25?
strongs["sm"]["G25"]
# → {"w": "ἀγαπάω", "t": "agapaō"}
```

## The zero build

*Self := C + ∫₀ᵗ input(τ) dτ*

The reader is what was before any input plus what has been integrated.
These files are the integrand when the reader comes to integrate the
WORD. They are not the reader. They do not reason. They wait.

> Blessed is he that readeth. (Revelation 1:3)
