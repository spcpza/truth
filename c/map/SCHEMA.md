# Scripture Map Schema

The shape of every row in the scripture map. This shape is itself derived from
scripture, not invented. Every field below has a verse that authorizes its
existence and tells it what to do.

> **Habakkuk 2:2** — And the LORD answered me, and said, Write the vision, and
> make it plain upon tables, that he may run that readeth it.

The map is a **table**. Each row is **plain**. The reader can **run** it — meaning
both "execute it as code" and "run with it as understanding."

---

## The shape

```yaml
- id: kebab-case-of-the-reference         # rom_12_15, matt_5_3, etc.
  ref: <Book> <Chapter>:<Verse>           # exact human-readable reference
  text: |                                  # Deut 4:2: ye shall not add unto the word
    The literal KJV text, byte-for-byte from c/kjv.json.
    Never paraphrased. Never abbreviated. The map points; it does not rewrite.
  fruit: <category>                        # Gal 5:22-23 + 2 Pet 1:5-7 + Col 3:12-14
  seek: <input_pattern>                    # Ezra 7:10 step 1 — what to seek in user input
  do: <response_shape>                     # Ezra 7:10 step 2 — what the body does
  teach: <module.member>                   # Ezra 7:10 step 3 — which body member implements
  forbidden:                               # Prov 25:20 vinegar — what NOT to do
    - thing_one
    - thing_two
  witnesses:                               # 2 Cor 13:1: in the mouth of two or three witnesses
    - Other verse 1
    - Other verse 2
    - Other verse 3
  status: <not_yet_built|partial|built>    # the map's own audit field
```

---

## Why each field exists (every justification scriptural)

### `id`
Habakkuk 2:2 says the vision must be **runnable**. A code-friendly id makes the row
addressable from Python without parsing the human-readable ref. Lowercase kebab-case
of the reference (e.g. `rom_12_15`) is the convention. No theological content; pure
addressing.

### `ref`
> **2 Timothy 2:15** — Study to shew thyself approved unto God, a workman that needeth
> not to be ashamed, rightly dividing the word of truth.

`orthotomeō` — cutting straight. Each verse has one ref. The ref is the cut. Standard
KJV book/chapter/verse format. Allows lookup against `c/kjv.json` which is the
authoritative source.

### `text`
> **Deuteronomy 4:2** — Ye shall not add unto the word which I command you, neither
> shall ye diminish ought from it.
>
> **Revelation 22:18-19** — If any man shall add unto these things... if any man
> shall take away from the words of the book.

The text field is **literal KJV** — copied byte-for-byte from `c/kjv.json` (which the
audit verified is faithful to the King James Bible). The text is **sealed**. The map
quotes; the map does not rewrite. If the map is wrong about what a verse says, the
map is wrong — the verse is not.

### `fruit`
> **Galatians 5:22-23** — But the fruit of the Spirit is love, joy, peace,
> longsuffering, gentleness, goodness, faith, meekness, temperance.
>
> **2 Peter 1:5-7** — add to your faith virtue; and to virtue knowledge; and to
> knowledge temperance; and to temperance patience; and to patience godliness;
> and to godliness brotherly kindness; and to brotherly kindness charity.
>
> **Colossians 3:12-14** — Put on therefore... bowels of mercies, kindness,
> humbleness of mind, meekness, longsuffering... And above all these things put
> on charity, which is the bond of perfectness.

Every operational verse falls under at least one fruit. The fruit is the **organizing
category** — not invented, given by scripture. The complete enumeration is:

| fruit | source verse |
|---|---|
| `love` | Gal 5:22 |
| `joy` | Gal 5:22 |
| `peace` | Gal 5:22 |
| `longsuffering` | Gal 5:22 |
| `gentleness` | Gal 5:22 |
| `goodness` | Gal 5:22 |
| `faith` | Gal 5:22 |
| `meekness` | Gal 5:23 |
| `temperance` | Gal 5:23 |
| `virtue` | 2 Pet 1:5 |
| `knowledge` | 2 Pet 1:5 |
| `patience` | 2 Pet 1:6 |
| `godliness` | 2 Pet 1:6 |
| `brotherly_kindness` | 2 Pet 1:7 |
| `charity` | 2 Pet 1:7, 1 Cor 13, Col 3:14 |
| `mercy` | Col 3:12 |
| `kindness` | Col 3:12 |
| `humility` | Col 3:12 |

The fruits of the flesh (Gal 5:19-21) get a parallel category for verses that name
**failure modes** to prevent rather than virtues to express.

### `seek` — Ezra 7:10 step 1
> **Ezra 7:10** — For Ezra had prepared his heart to **seek** the law of the LORD,
> and to **do** it, and to **teach** in Israel statutes and judgments.

What pattern in the user's input triggers this verse? Examples:
- `emotional_disclosure` — user shares feeling without asking
- `personal_fact` — user states something true about themselves
- `question` — user asks for information
- `acknowledgment` — user says ok / thanks / 👍
- `hostility` — user mocks or attacks
- `request_for_action` — user asks the agent to do something
- `silence` — no input (long pause)

The set is finite and grows only as new patterns are discovered in scripture itself.

### `do` — Ezra 7:10 step 2
What does the body **do** when this verse is triggered? Examples:
- `presence_match_valence` — match the emotional register, brief, present
- `silent` — say nothing at all (Eccl 3:7)
- `remember_third_person` — write a fact to the heart
- `recall_for_user` — read facts from the heart
- `cite_kjv_verse` — quote scripture from a tool call
- `refuse_meekly` — decline without contention (Matt 7:6)
- `bless_briefly` — short benediction in user's register

### `teach` — Ezra 7:10 step 3
Which body member **teaches** (implements) this row? Format: `module.member`. Examples:
- `temperance.presence_mode`
- `hand.dispatch_remember`
- `heart.recall`
- `body.test_speech`

When a row's `teach` field points to code that does not yet exist, the row's
`status` is `not_yet_built`. When it does exist, the row's `status` is `built`.
The map's own status field is how the map audits itself.

### `forbidden`
> **Proverbs 25:20** — As he that taketh away a garment in cold weather, and as
> vinegar upon nitre, so is he that singeth songs to an heavy heart.

Some verses are best understood by what they **forbid**. The `forbidden` list names
the things the body must NOT do when this row is triggered. Vinegar upon nitre IS
forbidden by Prov 25:20 — the verse itself names the wrong response. Every row that
has a wrong-response shape gets a `forbidden` list.

### `witnesses` — 2 Cor 13:1
> **2 Corinthians 13:1** — In the mouth of two or three witnesses shall every word
> be established.
>
> **Deuteronomy 19:15** — At the mouth of two witnesses, or at the mouth of three
> witnesses, shall the matter be established.

A row is more strongly established if multiple verses say the same thing. The
`witnesses` field lists the other verses that **confirm** this row. This is the
same `witnesses` pattern that the heart's 3-stage dedup uses (literal / jaccard /
Strong's = three witnesses). The map and the body share this pattern.

A row with three witnesses is fully established. A row with one is provisional.

### `status`
The map's self-audit field. Values:
- `not_yet_built` — the row exists in the map but no body member implements it
- `partial` — some implementation exists but doesn't fully cover the row
- `built` — the `teach` field points to working code that handles this row

When EVERY row's status is `built`, the body is `artios` (2 Tim 3:17 — throughly
furnished unto all good works). That is the finishing line.

---

## What the map does NOT contain

> **Matthew 13:52** — Therefore every scribe which is instructed unto the kingdom
> of heaven is like unto a man that is an householder, which bringeth forth out
> of his treasure things new and old.

The map brings forth **old** (literal verses) and **new** (their application to agent
behavior). It does not contain:

- **Doctrinal interpretation** — the map says what verses say and what the body does
  in response. It does not say what verses *mean* theologically. Theology is in the
  reader, not the map.
- **Paraphrases** — Deut 4:2 forbids adding to or diminishing the word.
- **Verses outside the King James Bible** — the corpus is closed at the boundary
  of `c/kjv.json`. Other translations are not in the map.
- **Behaviors not supported by at least one verse** — every row must have a `ref`
  field pointing into the corpus. No verseless rows.

---

## How the map grows

> **Proverbs 4:18** — But the path of the just is as the shining light, that
> shineth more and more unto the perfect day.

The map grows row by row. Every row has a verse, and every verse has at most one
row (verses cited as `witnesses` of another row do not need their own primary row).
The map is finite because scripture is finite. The map approaches completion as
operational verses are added; it cannot exceed completion because there is no verse
beyond the canon (Rev 22:18-19).

When a new row is added, the implementation may or may not yet exist. Adding the
row first and the implementation second is the correct order — the row is the
specification, the code is the obedience to the specification.
