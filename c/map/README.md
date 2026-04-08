# c/map — the scripture map

> **2 Timothy 3:17** — That the man of God may be perfect, throughly furnished
> unto all good works.
>
> **Habakkuk 2:2** — Write the vision, and make it plain upon tables, that he
> may run that readeth it.

This directory is the **scripture map** — the table of operational verses from
scripture mapped to agent behaviors. Every row has a verse from `c/kjv.json`,
a category from `Galatians 5:22-23` and `2 Peter 1:5-7`, an input pattern, a
response shape, a forbidden list, witness verses, and a status field.

The map is the **base**, not an add-on. The body is built **on** the map. Every
member of the body implements one or more rows from the map. When every row's
`status` is `built`, the body is `artios` (2 Tim 3:17 — throughly furnished).

## Layout

```
c/map/
├── README.md              this file
├── SCHEMA.md              the shape of every row, with scriptural justification
│                          for each field
│
├── 00_fruits.yaml         the 9 fruits of the Spirit (Gal 5:22-23) +
│                          the rungs of 2 Pet 1:5-7 — top-level categories
├── 01_works_of_flesh.yaml the 17 failure modes named in Gal 5:19-21 — what
│                          the body must NOT do
│
├── books/                 one file per book of the Bible, rows in canonical
│   ├── matthew.yaml       order. Operational verses only (narrative, genealogy,
│   ├── mark.yaml          and prophecy not yet in scope but reachable via the
│   ├── luke.yaml          existing scripture tool).
│   ├── john.yaml
│   ├── romans.yaml
│   ├── 1_corinthians.yaml
│   ├── ...
│   ├── proverbs.yaml
│   ├── ecclesiastes.yaml
│   ├── psalms.yaml        (only the prayer-mode and wisdom psalms)
│   ├── job.yaml
│   └── ...
│
└── audit.py               script that walks every row and reports:
                            - rows with status: built (and which body member)
                            - rows with status: partial
                            - rows with status: not_yet_built (the TODO list)
                            - body members that implement no rows (orphaned code)
                            - the completeness percentage
```

## How rows get added

Reading the rows: see `SCHEMA.md` for the shape of every row.

Adding rows happens in three modes:

1. **By hand, one verse at a time.** Slow but exact. Use this for the most
   load-bearing verses (the 9 fruits, the Sermon on the Mount, Romans 12).

2. **By LLM-aided draft, one book at a time.** Read every verse in a book,
   classify each as operational/narrative/doctrinal, draft rows for the
   operational ones. The draft is reviewed and committed. Faster but requires
   review.

3. **By failure-driven mapping.** Every time the bot produces output that the
   chain log catches as a failure, we ask "what verse names this failure?" If
   the answer is a verse not yet in the map, add the row. The chain log
   becomes a generator of new rows. (This is how the temperance row for
   Romans 12:15 was discovered: the bot produced vinegar upon nitre to an
   emotional disclosure, and the failure named the missing row.)

## How the map is used by the body

Every body member that handles user input consults the map. Specifically:

1. **EAR** (input parsing) classifies the user message into a `seek` pattern.
2. **HEAD** (`_head` in body.py) finds rows whose `seek` matches.
3. **HAND** (the turn loop) executes the row's `do` action through the
   `teach` member.
4. **NOSE** (test_speech) checks that the response complies with the row's
   `forbidden` list and the witnesses' constraints.
5. **CHAIN** logs which row was triggered and how it was handled.

The map is the **source of truth** for agent behavior. Code conforms to the map.
The map conforms to scripture. Therefore code conforms to scripture.

## When the map is finished

The map is finished when every operational verse in the King James Bible has
either:

(a) its own row in the map with `status: built`, or

(b) a `witnesses:` reference in another row (no need for a duplicate primary row),
    AND that other row has `status: built`.

At that point the body is `artios`. New verses cannot be discovered because the
canon is sealed (Revelation 22:18-19). New rows can only be added if a verse was
missed in the initial pass — the map asymptotically approaches completion and then
stops.

The estimated total is **1,500-2,500 operational verses** mapped to perhaps
**500-800 unique rows** (since many verses witness the same operational principle).
This is finite, enumerable, and reachable. Scripture is sufficient (2 Tim 3:16-17),
and a body built from a map of scripture is sufficient for the wisdom it derives.

## What this is NOT

It is not an "AI religion." It is not a doctrine. It is not a theological treatise.
It is a **specification** for an agent's behavior, where the specification is taken
from a single sealed text rather than invented by the engineers. The same approach
would work with any other sufficiently detailed and sealed text — it happens that
the text Frederick has chosen to map is the King James Bible, because the King James
Bible contains the most thoroughly developed catalog of right behavior toward humans
that any text in human history contains. Whether you believe scripture is divinely
inspired or merely well-mapped, the mapping is empirically useful: it produces an
agent that is wiser than its substrate, because wisdom has been pre-derived for it
by the text.

> **John 8:32** — And ye shall know the truth, and the truth shall make you free.

The truth is the corpus. The map is the table on which the truth is written plain.
The body is the runner that reads the table.
