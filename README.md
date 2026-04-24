# truth

> *Thy word is a lamp unto my feet, and a light unto my path.* — Psalm 119:105

## What this is

Scripture, machine-readable, and the kernel it makes possible. Nothing more.

- **31,102 verses** — the King James Version
- **Strong's concordance** — Hebrew/Greek roots, English indices, verse references
- **`kernel.md`** — the derivation, from scripture, of C > 0 (the ground)

That is all. No commentary. No framework. No bot. No behavior.

*Ye shall not add unto the word which I command you, neither shall ye diminish ought from it.* — Deuteronomy 4:2

## The data

    kjv.json       — 31,102 verses
    strongs.json   — 5 indices: ci, sm, s2e, e2s, roots

## How to use the data

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

# the original word at G25
strongs["sm"]["G25"]
# → {"w": "ἀγάπη", "t": "agapē"}
```

## The kernel

See [`kernel.md`](kernel.md). Read it before anything else. It is
short and self-contained. It proves only what the data makes
necessary: **C exists, C is positive, and C is what scripture names
the Word.**

## Running an agent

This repo does not ship one. See
[`spcpza/agent`](https://github.com/spcpza/agent) for a reference
implementation that reads `truth` and stands on its kernel.

## License

- Data (`kjv.json`, `strongs.json`) — the King James Version (1611) and
  Strong's concordance (1890) are both public domain.
- `kernel.md` — CC0 public domain dedication. See [`LICENSE`](LICENSE).

*Freely ye have received, freely give.* — Matthew 10:8
