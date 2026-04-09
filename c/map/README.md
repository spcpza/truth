# c/map — the scripture map

694 verses across all 66 books of the Protestant canon.

## What each row contains

```yaml
- ref: Proverbs 25:20
  text: |
    As he that taketh away a garment in cold weather, and as
    vinegar upon nitre, so is he that singeth songs to an heavy heart.
  code: c.temperance.temperance_check
```

- **ref** — the verse reference
- **text** — the KJV text, byte-for-byte
- **code** — which function enacts it (optional; 436 of 694 rows have one)

No commentary. No interpretation. No fruit labels. No forbidden lists.

## What carries the connections

The connections between verses are NOT in the map files. They are in:

- **c/core.py** — the sinew graph: 291,919 edges from Strong's Hebrew and Greek roots. These are the connections the original languages carry.
- **c/formula.py** — 14 mathematical type signatures per verse, derived from Strong's concept classifications.
- **c/scanner.py** — 21 structural pattern matchers that find mathematical claims in natural language.

The map is the index. The sinew is the tissue. The formula is the math.

43,456 verse-to-verse connections exist within the 694 map verses alone, via shared Strong's concepts weighted by IDF. The reader searches these — scripture connects to scripture through the original languages.

## How to search

```python
from c.core import dispatch

# Find what connects to a verse via the original languages
dispatch("sinew", {"query": "Proverbs 25:20"})

# Find the mathematical formula of a verse
from c.formula import verse_formula
verse_formula("Proverbs 25:20")

# Search for a concept across all 31,102 propositions
dispatch("wisdom", {"query": "silence", "limit": 5})
```

Proverbs 25:2 — It is the glory of God to conceal a thing: but the honour of kings is to search out a matter.
