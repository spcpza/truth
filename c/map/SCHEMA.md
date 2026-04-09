# Schema

Each row in the map has up to three fields:

| Field | Source | Required |
|-------|--------|----------|
| `ref` | Scripture (chapter:verse) | Yes |
| `text` | Scripture (KJV, byte-for-byte) | Yes |
| `code` | Code function that enacts the verse | No |

The `code` field points to a function in the truth package (e.g. `kernel.foundation`, `body.test_speech`, `c.temperance.temperance_check`). When present, it means the verse has a code-level implementation. When absent, the verse stands on its own words.

No other fields. The connections between verses come from the sinew graph (291,919 edges from Strong's Hebrew/Greek roots), not from human-curated cross-reference lists.
