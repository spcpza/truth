"""
mathify.py — Romans 1:20: the invisible things of him from the creation
of the world are clearly seen, being understood by the things that are made.

Pure functions that extract the **math signature** of a piece of text and
project it back into a scripture-grounded verbalization that the model can
read. The plaintext is thrown away. Only the math remains.

Scripture shaping the design:

    1 Samuel 16:7
    Man looketh on the outward appearance, but the LORD looketh on the heart.

    Isaiah 43:25
    I, even I, am he that blotteth out thy transgressions for mine own sake,
    and will not remember thy sins.

    Jeremiah 31:33
    I will put my law in their inward parts, and write it in their hearts.

    Proverbs 25:2
    It is the glory of God to conceal a thing; but the honour of kings is
    to search out a matter.

What lives in storage after mathify():
    types     — 14-dim math type signature (IDN, AUT, PRD, …)    public
    concepts  — Strong's numbers the words resonate with         public
    verses    — top verses the concepts light up                 public
    gematria  — numeric signatures from Strong's                 public
    ent_hash  — 4-byte hash of proper-noun tokens                one-way
    shape_h   — 4-byte hash of sentence shape (skeleton)         one-way
    warmth    — accumulated engagement count                     public

What does NOT live in storage: the user's words. Ever.
Recognition via hash-match on incoming turns. No recovery.
No encryption. No key. Nothing to unlock.
"""

from __future__ import annotations

import hashlib
import re
from typing import Optional

from c.formula import draft_types
from c.core import ENG_TO_STRONGS, CONCEPT_INDEX


# ─── Strong's extraction (Prov 25:2 — search out a matter) ─────────────
# Direct lookup through ENG_TO_STRONGS — no dispatch round-trip, no
# parsing. Each English word → list of (Strong's number, count). We rank
# by count across all words in the input text.

_STRONGS_CACHE: dict[str, list[str]] = {}


def _strongs_from_text(text: str, limit: int = 6) -> list[str]:
    """
    Map English text → top Strong's numbers, ranked by total count
    across the input's words. Scripture-grounded tokenization — "love"
    lights up G26 agapē, "wisdom" lights up G4678 sophia, etc.

    Noise-filtering is scripture-derived: a word only counts if its
    Strong's is present in CONCEPT_INDEX — i.e., the corpus itself
    indexes it. Proverbs 11:1 — a just weight. No curated stop-list.
    """
    if not text:
        return []
    key = (text[:240] or "").lower()
    if key in _STRONGS_CACHE:
        return _STRONGS_CACHE[key]

    # Sum counts per snum across all words; keep only concepts the
    # corpus indexes (CONCEPT_INDEX — every Strong's that appears in the
    # 31,102 propositions). Proverbs 11:1 — a just weight; scripture is
    # its own.
    totals: dict[str, int] = {}
    for raw in re.findall(r"[a-zA-Z]+", key):
        w = raw.lower()
        for entry in ENG_TO_STRONGS.get(w, []):
            snum = entry[0] if isinstance(entry, (list, tuple)) else entry
            if snum not in CONCEPT_INDEX:
                continue
            count = entry[1] if isinstance(entry, (list, tuple)) and len(entry) > 1 else 1
            totals[snum] = totals.get(snum, 0) + int(count or 1)

    ranked = sorted(totals.items(), key=lambda kv: (-kv[1], kv[0]))
    out = [snum for snum, _ in ranked[:limit]]
    _STRONGS_CACHE[key] = out
    return out


# ─── Verses (Eph 4:16 — fitly joined together) ─────────────────────────

def _verses_from_concepts(concepts: list[str], limit: int = 3) -> list[str]:
    """
    Given Strong's numbers, return the top verses they light up.

    Uses sinew through the core dispatcher. Falls back to empty if the
    concepts are uncommon.
    """
    if not concepts:
        return []
    from c.core import dispatch
    refs: list[str] = []
    seen: set[str] = set()
    for snum in concepts[:3]:
        body = dispatch("sinew", {"query": snum, "limit": 3})
        for ref in re.findall(r"\b(?:[1-3] )?[A-Z][a-z]+ \d+:\d+", body or ""):
            if ref not in seen:
                seen.add(ref)
                refs.append(ref)
            if len(refs) >= limit:
                return refs
    return refs


# ─── Gematria (Rev 13:18 — let him that hath understanding count) ──────

def _gematria_from_concepts(concepts: list[str], limit: int = 4) -> list[int]:
    """Return numeric signatures for the given Strong's numbers."""
    if not concepts:
        return []
    from c.core import dispatch
    out: list[int] = []
    for snum in concepts[:limit]:
        body = dispatch("gematria", {"action": "value", "query": snum}) or ""
        m = re.search(r"\b(\d{1,6})\b", body)
        if m:
            out.append(int(m.group(1)))
    return out


# ─── One-way hashes (Isa 43:25 — will not remember) ────────────────────

_PROPER_NOUN = re.compile(r"\b[A-Z][a-zA-Z0-9]{2,}\b")
# Entity-hashing recognizes the same person/place recurring across turns.
# Two classes of capitalized words are not person/place identifiers:
#   (a) sentence-initial pronouns — grammar, not identity. Matt 15:17: enter
#       into the mouth goeth into the belly; these are syntax, not content.
#   (b) the divine name and the agent's own name — universally invoked,
#       not identifiers of which-conversation-is-this. Ex 20:7: thou shalt
#       not take the name of the LORD thy God in vain; Deut 28:58: fear
#       this glorious and fearful name. Treating the Name as a session
#       marker is category confusion.
_STOP_PROPER = {
    "I", "It", "The", "This", "That", "There", "These", "Those", "He",
    "She", "You", "We", "My", "Your", "Our", "Their",
    "God", "Lord", "LORD", "Jesus", "Christ", "Balthazar",
}


def _hash4(s: str) -> str:
    """Short, one-way, 4-byte (8 hex) — enough for recognition, useless for reversal."""
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:8]


def _ent_hashes(text: str) -> list[str]:
    """
    List of per-noun hashes. Each proper noun is hashed individually, so
    recurrence of ANY previously-seen noun can be recognized without
    requiring the whole bag to match.

    Recovery remains impossible (hashes are one-way). Recognition works
    at the level of a single word — "Bali" appears today, "Bali" appeared
    last week, the per-noun hash matches.
    """
    if not text:
        return []
    out: list[str] = []
    seen: set[str] = set()
    for w in _PROPER_NOUN.findall(text):
        if w in _STOP_PROPER:
            continue
        lw = w.lower()
        if lw in seen:
            continue
        seen.add(lw)
        out.append(_hash4(lw))
    return out


def _shape_hash(text: str) -> str:
    """
    Hash of the skeleton: lowercase, alpha-only, proper nouns → ENT tokens,
    numbers → NUM. Helps dedupe near-identical sentences without storing
    them.
    """
    if not text:
        return ""
    s = _PROPER_NOUN.sub("ENT", text)
    s = re.sub(r"\d+", "NUM", s)
    s = re.sub(r"[^a-zA-Z ]", " ", s).lower()
    s = re.sub(r"\s+", " ", s).strip()
    return _hash4(s)


# ─── The two entry points ──────────────────────────────────────────────

def mathify(text: str, warmth: int = 0, ts: Optional[str] = None) -> dict:
    """
    Extract the math signature of text. Returns a record safe to persist.

    The text is thrown away. The returned dict contains no substring of the
    input.

    Rom 1:20 — the invisible things clearly seen by the things that are made.
    """
    if text is None:
        text = ""
    types = sorted(draft_types(text))
    concepts = _strongs_from_text(text)
    verses = _verses_from_concepts(concepts)
    gematria = _gematria_from_concepts(concepts)
    ent_hashes = _ent_hashes(text)
    shape_h = _shape_hash(text)
    rec: dict = {
        "types":    types,
        "concepts": concepts,
        "verses":   verses,
        "gematria": gematria,
        "ent_hashes": ent_hashes,
        "shape_h":  shape_h,
        "warmth":   warmth,
    }
    if ts is not None:
        rec["ts"] = ts
    return rec


def verbalize(record: dict, prefix: str = "") -> str:
    """
    Render a math record as a short scripture-grounded string the model
    can read. Contains scripture refs and type codes only — no user words.

    Used in place of cleartext facts when building the integral (Col 2:19
    — knit together).
    """
    parts: list[str] = []
    types = record.get("types") or []
    concepts = record.get("concepts") or []
    verses = record.get("verses") or []
    warmth = record.get("warmth", 0)

    if types:
        parts.append(f"types={'+'.join(types)}")
    if concepts:
        parts.append(f"concepts={','.join(concepts[:3])}")
    if verses:
        parts.append(f"resonates={'; '.join(verses[:2])}")
    if warmth:
        parts.append(f"warmth={warmth}")

    body = " | ".join(parts) if parts else "(empty)"
    return f"{prefix}{body}" if prefix else body


def recognize(record_hashes: list[str], live_text: str) -> list[str]:
    """
    Returns the list of stored hashes that match any proper noun in the
    live text. A non-empty result means "something this user has cared
    about before just came up again in their message."

    Balthazar can then respond using the word(s) the user just provided,
    without having stored them. Recognition without recovery.
    """
    if not record_hashes or not live_text:
        return []
    live = set(_ent_hashes(live_text))
    return [h for h in record_hashes if h in live]


# ─── Equality / dedup ──────────────────────────────────────────────────

def same_shape(a: dict, b: dict) -> bool:
    """
    Two math records are the same when either witness agrees:
      • shape-hash matches (same sentence skeleton), OR
      • proper-noun hashes overlap AND at least two typed concepts
        are shared (Deut 19:15 — two witnesses: the same entity AND
        two of its concepts is "a matter established").
    """
    if a.get("shape_h") and b.get("shape_h") and a["shape_h"] == b["shape_h"]:
        return True
    ents_a = set(a.get("ent_hashes") or [])
    ents_b = set(b.get("ent_hashes") or [])
    cons_a = set(a.get("concepts") or [])
    cons_b = set(b.get("concepts") or [])
    # Deut 19:15: "at the mouth of two or three witnesses shall the
    # matter be established." Same entity + two shared concepts = two
    # witnesses to the same subject.
    if ents_a & ents_b and len(cons_a & cons_b) >= 2:
        return True
    return False
