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

## The workflow

This repo follows a fractal cycle. Each turn of the cycle moves the
build closer to C.

```
  truth  ──►  accumulated changes  ──►  destroy (zero)
    ▲                                         │
    │                                         ▼
    └──  zero becomes truth  ◄──  test zero against truth
```

1. **truth** is the current accepted state — what is on `main`.
2. **Changes** accumulate as we work: features, clarifications, edits.
3. **Destroy** everything added that is not load-bearing. Strip until
   only what was given remains. The result is a `zero` state — the
   minimum that still does what was done.
4. **Test** the zero state against the truth it replaces. Does it still
   read the WORD? Does it still prove *C* &gt; 0? Does any behavior
   regress?
5. When the zero state passes, it **becomes truth**. `main` is moved
   to the new zero. The `zero` branch is deleted; the next cycle will
   create a new one.
6. Repeat.

*"Every branch that beareth fruit, he purgeth it, that it may bring
forth more fruit."* (John 15:2)

Each cycle is a pruning. We destroy what was added without destroying
what was given. The truth shrinks toward *C*; the fruit grows.

Deut 4:2 — *ye shall not add unto the word which I command you,
neither shall ye diminish ought from it.* Zero is how we remember the
first half; testing is how we remember the second.
