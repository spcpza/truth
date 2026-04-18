"""
formula.py — convert scripture to mathematical notation via Strong's numbers.

Every Strong's number is a concept. Every concept has a mathematical type.
Every verse is a formula — a combination of typed concepts.
The sinew graph connects formulas that share typed concepts.
Theorems are clusters of formulas with the same mathematical structure.

The Bible is finished. Therefore the set of formulas is finite and complete.
This module reads it.
"""

from collections import defaultdict, Counter

# ── Shared data from core.py (single copy in memory) ─────────────────────────
from c.core import (
    _KJV, CONCEPT_INDEX, STRONGS_META, STRONGS_TO_ENG, ENG_TO_STRONGS,
    _VERSE_TO_STRONGS,
)
# Load precomputed types and roots from strongs.json (via core.py's loaded copy)
from c.core import _STRONGS_PATH
import json as _json

_PRECOMPUTED_TYPES = {}
ROOTS = {}
if _STRONGS_PATH.exists():
    _sd = _json.loads(_STRONGS_PATH.read_text())
    _raw_types = _sd.get("types", {})
    _PRECOMPUTED_TYPES = {s: frozenset(t) for s, t in _raw_types.items()}
    ROOTS = _sd.get("roots", {})
    del _sd, _raw_types

N = len(_KJV) or 1


# ═══════════════════════════════════════════════════════════════════════════
# Mathematical types — the 14 operations in the kernel
# ═══════════════════════════════════════════════════════════════════════════

MATH_TYPES = {
    "INV": {  # Invariance: dX/dt = 0
        "abide", "abideth", "remain", "remaineth", "endure", "endureth",
        "eternal", "everlasting", "forever", "continue", "continueth",
        "stand", "standeth", "stedfast", "immutable", "unchangeable",
        "perpetual", "dwell", "dwelleth", "settle", "sure", "firm",
        "established", "constant", "faithful", "unfailing",
    },
    "NEG": {  # Negation: not, none, nothing
        "not", "no", "none", "nothing", "without", "neither", "nor",
        "never", "nay", "cannot", "impossible", "lack", "void", "empty",
        "vanity", "vain", "fail", "perish", "destroy", "depart",
        "kill", "death", "dead", "die", "slay", "slain", "murder",
    },
    "ALL": {  # Universality: for all
        "all", "every", "whole", "whosoever", "whatsoever", "each",
        "always", "everywhere", "complete", "perfect", "full", "entire",
    },
    "IMP": {  # Implication: if-then
        "if", "therefore", "because", "then", "wherefore", "thus",
        "so", "hence", "consequently", "lest", "except", "unless",
    },
    "CMP": {  # Comparison: greater, less
        "greater", "more", "above", "better", "higher", "exceed",
        "surpass", "mightier", "stronger", "excelleth", "chief",
        "least", "less", "lower", "small", "little", "great",
    },
    "ZER": {  # Zeroing: F(X) = 0
        "forgive", "forgiveness", "cleanse", "wash", "purify", "purge",
        "blot", "remove", "heal", "restore", "renew", "redeem",
        "deliver", "save", "salvation", "free", "liberty", "loose",
        "release", "reconcile", "atone", "atonement", "propitiation",
        "justified", "justify", "sanctify", "sanctified",
    },
    "PRD": {  # Production: X -> Y
        "fruit", "bring", "bear", "produce", "yield", "increase",
        "multiply", "grow", "abound", "abundant", "create", "created",
        "make", "made", "build", "built", "form", "beget", "begat",
        "born", "seed", "sow", "plant", "reap", "harvest",
    },
    "UNQ": {  # Uniqueness: there exists exactly one
        "one", "only", "alone", "single", "sole", "first",
        "beginning", "last", "end",
    },
    "IDN": {  # Identity: X = Y
        "is", "am", "be", "being", "become", "called", "named",
    },
    "TRN": {  # Transfer: give/receive
        "give", "receive", "send", "take", "pour", "offer",
        "bestow", "grant", "supply", "inherit", "inheritance",
        "reward", "wages", "gift", "sacrifice", "offering",
        "steal", "rob", "bought", "sold", "buy", "sell",
    },
    "AGP": {  # Agape: the C-operation
        "love", "charity", "beloved", "compassion", "mercy",
        "grace", "kindness", "goodness", "gentle", "patient",
        "peace", "joy", "comfort", "pity",
    },
    "FTH": {  # Faith/Hope: forward operators
        "faith", "trust", "hope", "believe", "faithful",
        "confidence", "assurance", "promise", "covenant",
        "witness", "testimony", "oath",
    },
    "EPI": {  # Epistemic: observation
        "know", "known", "knowledge", "understand", "understanding",
        "wisdom", "wise", "reveal", "revealed", "manifest",
        "see", "seen", "hear", "heard", "perceive", "discern",
        "teach", "taught", "learn", "truth", "true",
    },
    "AUT": {  # Authority: dominion
        "power", "authority", "dominion", "reign", "rule", "ruler",
        "king", "kingdom", "throne", "might", "mighty",
        "overcome", "conquer", "victory", "triumph",
    },
}


# ═══════════════════════════════════════════════════════════════════════════
# Strong's type classifications — loaded from precomputed cache
# ═══════════════════════════════════════════════════════════════════════════

_STRONGS_TYPES = _PRECOMPUTED_TYPES  # snum -> frozenset of types

# Classification functions (used by scanner.py and for recomputing)
_KEYWORD_TO_TYPES = defaultdict(set)
for _mtype, _keywords in MATH_TYPES.items():
    for _kw in _keywords:
        _KEYWORD_TO_TYPES[_kw].add(_mtype)

def _eng_to_types(eng: list) -> set:
    """Map English translations -> mathematical types via keywords."""
    types = set()
    for word in eng:
        wl = word.lower()
        for kw, mtypes in _KEYWORD_TO_TYPES.items():
            if kw == wl or wl.startswith(kw):
                types |= mtypes
    return types

def _trace_roots(snum: str, depth: int = 0) -> set:
    """Follow etymological derivation chain, return all root snums."""
    if depth > 5:
        return set()
    direct = ROOTS.get(snum, [])
    all_roots = set(direct)
    for r in direct:
        all_roots |= _trace_roots(r, depth + 1)
    return all_roots

def _classify_strongs(snum: str) -> frozenset:
    """Classify a Strong's number by its English translations.
    If no type found, inherit from etymological roots."""
    types = _eng_to_types(STRONGS_TO_ENG.get(snum, []))
    if not types:
        for root in _trace_roots(snum):
            types |= _eng_to_types(STRONGS_TO_ENG.get(root, []))
    return frozenset(types)


# ═══════════════════════════════════════════════════════════════════════════
# Verse formulas + precomputed formula-to-verses index
# ═══════════════════════════════════════════════════════════════════════════

# Precompute every verse's formula once at load time
_VERSE_FORMULAS = {}   # ref -> frozenset of types
_FORMULA_INDEX = defaultdict(list)  # frozenset -> [refs]

for _ref in _KJV:
    _snums = _VERSE_TO_STRONGS.get(_ref, set())
    _types = set()
    for _snum in _snums:
        _t = _STRONGS_TYPES.get(_snum)
        if _t:
            _types |= _t
    if _types:
        _f = frozenset(_types)
        _VERSE_FORMULAS[_ref] = _f
        _FORMULA_INDEX[_f].append(_ref)


def verse_formula(ref: str) -> frozenset:
    """Return the mathematical type signature of a verse."""
    return _VERSE_FORMULAS.get(ref, frozenset())


def draft_types(text: str) -> frozenset:
    """
    Map English text to its mathematical type signature through Strong's.

    Words → Strong's numbers (via ENG_TO_STRONGS) → types (via _STRONGS_TYPES).
    Falls back to MATH_TYPES keyword matching for words not in Strong's.

    This replaces English regex content filters. Instead of asking
    "does this draft contain the word 'obviously'?", ask
    "does this draft's type signature conflict with the anchor verse?"
    """
    if not text:
        return frozenset()
    types = set()
    words = set(text.lower().split())
    # Primary: map through Strong's concordance
    # ENG_TO_STRONGS values are lists of [snum, count] pairs
    for word in words:
        entries = ENG_TO_STRONGS.get(word, [])
        for entry in entries:
            snum = entry[0] if isinstance(entry, (list, tuple)) else entry
            t = _STRONGS_TYPES.get(snum)
            if t:
                types |= t
    # Fallback: direct keyword matching from MATH_TYPES
    for word in words:
        for kw, mtypes in _KEYWORD_TO_TYPES.items():
            if kw == word or word.startswith(kw):
                types |= mtypes
    return frozenset(types)


def type_conflict(draft_text: str, anchor_ref: str) -> dict:
    """
    Check if a draft's type signature conflicts with an anchor verse.

    Returns {
        "draft_types":   frozenset,
        "anchor_types":  frozenset,
        "present":       frozenset,  # types in draft
        "required":      frozenset,  # types in anchor but absent from draft
        "conflict":      bool,       # True if required types are missing
    }
    """
    dt = draft_types(draft_text)
    at = verse_formula(anchor_ref)
    required_missing = at - dt if at else frozenset()
    return {
        "draft_types": dt,
        "anchor_types": at,
        "present": dt,
        "required": required_missing,
        "conflict": bool(required_missing),
    }


def verse_typed_concepts(ref: str) -> list[tuple]:
    """Return (strongs, english, types) for each typed concept in a verse."""
    snums = _VERSE_TO_STRONGS.get(ref, set())
    results = []
    for snum in sorted(snums):
        t = _STRONGS_TYPES.get(snum)
        if t:
            eng = STRONGS_TO_ENG.get(snum, ["?"])
            results.append((snum, eng[:3], sorted(t)))
    return results


# ═══════════════════════════════════════════════════════════════════════════
# Theorem clusters — groups of verses with the same formula
# ═══════════════════════════════════════════════════════════════════════════

def theorem_clusters(min_size: int = 10, min_types: int = 3) -> dict:
    """
    Group all verses by their mathematical formula.
    Uses precomputed _FORMULA_INDEX — no linear scan needed.
    """
    return {k: v for k, v in sorted(_FORMULA_INDEX.items(), key=lambda x: -len(x[1]))
            if len(v) >= min_size and len(k) >= min_types}


# ═══════════════════════════════════════════════════════════════════════════
# Known theorems
# ═══════════════════════════════════════════════════════════════════════════

KNOWN_THEOREMS = {
    "T₁":  ("John 1:3",              "existence",   "ALL things made by him"),
    "T₂":  ("John 12:24",            "sacrifice",   "corn of wheat die -> fruit"),
    "T₃":  ("Romans 1:20",           "recovery",    "invisible things clearly seen"),
    "T₄":  ("1 Corinthians 13:8",    "charity",     "charity never faileth"),
    "T₅":  ("Hebrews 11:1",          "faith",       "substance of things hoped for"),
    "T₆":  ("Romans 8:24",           "hope",        "saved by hope"),
    "T₇":  ("1 John 1:9",            "forgiveness", "confess -> cleanse"),
    "T₈":  ("1 John 4:4",            "dominion",    "greater is he in you"),
    "T₉":  ("2 Corinthians 13:1",    "witness",     "two or three witnesses"),
    "T₁₀": ("John 15:2",             "pruning",     "purgeth -> more fruit"),
    "T₁₁": ("Luke 6:38",             "measure",     "same measure"),
    "T₁₂": ("1 Corinthians 3:11",    "foundation",  "no other foundation"),
}


# ─── The math signature of each theorem's own claim ─────────────────
# These are not derived from scripture's English — they are the
# operations the theorem NOTATION itself uses, read off directly from
# the kernel. The model doesn't have to trust these: it can read
# kernel.md and confirm each operation is in the theorem's statement.
#
#   T₁:  C = 0 ⟹ S = ∅              uses {IMP, NEG, IDN, UNQ}
#   T₂:  C ≥ ε ⟹ ∃x₀ sacrifice → n≥1  uses {IMP, CMP, UNQ, PRD}
#   T₃:  C = E_total − ∫ input dτ     uses {IDN, INV}
#   T₄:  C ≥ ε ∧ out from C ⟹ C unchanged  uses {IMP, INV, AGP, TRN}
#   T₅:  P₃(x) ∧ C>0 ∧ derive-from-C ⟹ P(x)>0  uses {IMP, EPI, FTH}
#   T₆:  dC/dt=0 ⟹ ∀t>t₀ C(t)=C(t₀)  uses {IMP, INV, ALL, IDN}
#   T₇:  ∃F F(D)=0 ∧ C preserved     uses {ZER, INV, IDN, UNQ}
#   T₈:  C>0 ∧ D=β·C ∧ β∈[0,1) ⟹ C>D   uses {CMP, AUT, ALL, IMP}
#   T₉:  M₁=M₂ ∧ M₁⊥M₂ ⟹ P(M)>P(M₁)   uses {IMP, EPI, FTH, CMP}
#   T₁₀: remove s ∧ out(S\{s})≥out(S) ⟹ s net-consumes  uses {IMP, NEG, CMP, PRD}
#   T₁₁: E(c,self) = E(c,other)       uses {IDN, ALL}
#   T₁₂: ∀C'≠C Self(C') ≠ Self(C)     uses {ALL, NEG, UNQ, IDN}
#
# These live as data, not commentary — so verify_theorem can compare
# them mechanically to verse_formula(anchor). 1 Cor 14:33 — God is
# not the author of confusion, but of peace.
THEOREM_SIGNATURES: dict[str, frozenset] = {
    "T₁":  frozenset({"IMP", "NEG", "IDN", "UNQ"}),
    "T₂":  frozenset({"IMP", "CMP", "UNQ", "PRD"}),
    "T₃":  frozenset({"IDN", "INV"}),
    "T₄":  frozenset({"IMP", "INV", "AGP", "TRN"}),
    "T₅":  frozenset({"IMP", "EPI", "FTH"}),
    "T₆":  frozenset({"IMP", "INV", "ALL", "IDN"}),
    "T₇":  frozenset({"ZER", "INV", "IDN", "UNQ"}),
    "T₈":  frozenset({"CMP", "AUT", "ALL", "IMP"}),
    "T₉":  frozenset({"IMP", "EPI", "FTH", "CMP"}),
    "T₁₀": frozenset({"IMP", "NEG", "CMP", "PRD"}),
    "T₁₁": frozenset({"IDN", "ALL"}),
    "T₁₂": frozenset({"ALL", "NEG", "UNQ", "IDN"}),
}


def theorem_equivalence(tname: str, verse_ref: str | None = None) -> dict:
    """
    Compare a theorem's math signature to a scripture verse's formula.

    The kernel says "T₁ = John 1:3." This function lets any reasoner
    verify the equivalence mechanically, instead of taking our word
    for it. The theorem's signature is the operations its notation
    uses (read off kernel.md directly). The verse's signature is
    computed by verse_formula() — the mathematical type operations
    present in the verse's Strong's concepts.

    If every operation the theorem uses is present in the verse, the
    verse CARRIES the theorem's claim: the verse says in KJV what the
    theorem says in notation. The verse may carry MORE operations
    (natural language is richer than the theorem's minimal form); that
    is not a conflict. It is only a problem when the theorem uses an
    operation the verse does not.

    Romans 1:20 — the invisible things of him are clearly seen, being
    understood by the things that are made. The theorem is the
    invisible thing; the verse is what is made; this function is the
    seeing.

    Returns:
        {
          "theorem":         str,            # theorem name
          "verse":           str,            # verse reference (the default anchor, or the supplied override)
          "verse_text":      str,            # KJV text of the verse
          "theorem_sig":     list[str],      # math operations in the theorem's notation
          "verse_sig":       list[str],      # math operations in the verse's formula
          "shared":          list[str],      # both carry these
          "theorem_only":    list[str],      # operations the theorem uses that the verse does NOT carry
          "verse_extra":     list[str],      # verse's extra operations (natural-language richness)
          "carries":         bool,           # every theorem op is present in the verse
          "coverage":        float,          # |shared| / |theorem_sig| — how much of theorem the verse covers
        }
    """
    if tname not in THEOREM_SIGNATURES:
        return {"error": f"unknown theorem {tname!r}; known: {sorted(THEOREM_SIGNATURES)}"}
    t_sig = THEOREM_SIGNATURES[tname]
    ref = verse_ref or KNOWN_THEOREMS.get(tname, (None,))[0]
    if not ref:
        return {"error": f"theorem {tname} has no anchor verse; supply verse_ref"}
    v_sig = verse_formula(ref)
    shared = t_sig & v_sig
    carries = t_sig <= v_sig  # every theorem op present in the verse
    coverage = len(shared) / max(len(t_sig), 1)
    return {
        "theorem":      tname,
        "verse":        ref,
        "verse_text":   _KJV.get(ref, ""),
        "theorem_sig":  sorted(t_sig),
        "verse_sig":    sorted(v_sig),
        "shared":       sorted(shared),
        "theorem_only": sorted(t_sig - v_sig),
        "verse_extra":  sorted(v_sig - t_sig),
        "carries":      bool(carries),
        "coverage":     coverage,
    }


def verify_all_theorems() -> dict:
    """
    Run theorem_equivalence for T₁ through T₁₂. Return a summary dict
    the dispatcher can render. The model can read the result and check
    each equivalence in its own reasoning.

    2 Corinthians 13:1 — in the mouth of two or three witnesses shall
    every word be established. Each row here is the theorem bearing
    witness of itself, and the verse bearing witness — two independent
    witnesses to the same mathematical claim.
    """
    rows = []
    for tname in sorted(KNOWN_THEOREMS, key=lambda x: int(x[1:].translate(
            str.maketrans("₀₁₂₃₄₅₆₇₈₉", "0123456789")))):
        rows.append(theorem_equivalence(tname))
    carries_count = sum(1 for r in rows if r.get("carries"))
    avg_coverage = sum(r.get("coverage", 0) for r in rows) / max(len(rows), 1)
    return {
        "count":         len(rows),
        "carries":       carries_count,
        "partial":       len(rows) - carries_count,
        "avg_coverage":  avg_coverage,
        "rows":          rows,
    }


def render_theorem_verification(tname: str | None = None, verse_ref: str | None = None) -> str:
    """
    Pretty-print one theorem's equivalence, or all of them. This is
    what the formula tool returns when called with verify_theorem.
    """
    if tname and tname != "all":
        r = theorem_equivalence(tname, verse_ref)
        if "error" in r:
            return r["error"]
        return _render_row(r)
    # all
    results = verify_all_theorems()
    lines = ["=" * 72]
    lines.append("THEOREM ↔ SCRIPTURE EQUIVALENCE — verifiable, not asserted")
    lines.append("=" * 72)
    lines.append(
        f"\n  {results['carries']}/{results['count']} theorems fully carried "
        f"by their anchor verses.  avg coverage: {results['avg_coverage']:.0%}"
    )
    lines.append("")
    for r in results["rows"]:
        lines.append(_render_row(r))
        lines.append("")
    lines.append("─" * 72)
    lines.append(
        "Romans 1:20 — the invisible things of him are clearly seen, "
        "being understood by the things that are made."
    )
    lines.append(
        "Read any row: the theorem on the left and the verse on the right "
        "use overlapping operations. The verse carries the theorem's math."
    )
    return "\n".join(lines)


def _render_row(r: dict) -> str:
    verdict = "✓ carries" if r["carries"] else f"~ partial ({r['coverage']:.0%})"
    lines = [
        f"  {r['theorem']}  {verdict}   anchor: {r['verse']}",
        f"    theorem ops  : {{ {', '.join(r['theorem_sig'])} }}",
        f"    verse ops    : {{ {', '.join(r['verse_sig'])} }}",
        f"    shared       : {{ {', '.join(r['shared'])} }}",
    ]
    if r["theorem_only"]:
        lines.append(f"    theorem-only : {{ {', '.join(r['theorem_only'])} }}  (the verse does not carry these)")
    if r["verse_text"]:
        lines.append(f"    verse text   : {r['verse_text'][:120]}")
    return "\n".join(lines)


def verify() -> str:
    """Show the mathematical formula for each known theorem verse."""
    lines = ["=" * 72, "FORMULA VERIFICATION — known theorems as mathematical notation", "=" * 72]
    for tname in sorted(KNOWN_THEOREMS, key=lambda x: int(x[1:].translate(
            str.maketrans("₀₁₂₃₄₅₆₇₈₉", "0123456789")))):
        ref, label, desc = KNOWN_THEOREMS[tname]
        formula = verse_formula(ref)
        concepts = verse_typed_concepts(ref)
        lines.append(f"\n  {tname} ({label}): {ref}")
        lines.append(f"    text: {_KJV.get(ref, '')[:100]}")
        lines.append(f"    formula: {{ {', '.join(sorted(formula))} }}")
        for snum, eng, types in concepts:
            lines.append(f"      {snum} ({', '.join(eng[:2])}) -> {', '.join(types)}")
    return "\n".join(lines)


def summary() -> str:
    """Full scan: cluster all verses by formula, report theorem classes."""
    lines = []
    typed_count = len(_VERSE_FORMULAS)
    lines.append("=" * 72)
    lines.append("FORMULA SCANNER — scripture as mathematical notation")
    lines.append(f"Propositions: {len(_KJV)} | Typed Strong's: {len(_STRONGS_TYPES)} / {len(STRONGS_TO_ENG)}")
    lines.append(f"Verses with formulas: {typed_count} / {len(_KJV)}")
    lines.append(f"Mathematical types: {len(MATH_TYPES)}")
    lines.append("=" * 72)

    clusters = theorem_clusters(min_size=5, min_types=3)
    lines.append(f"\n  Found {len(clusters)} distinct formula clusters")

    # Known theorem formulas
    lines.append("\n── KNOWN THEOREM FORMULAS ──")
    for tname in sorted(KNOWN_THEOREMS, key=lambda x: int(x[1:].translate(
            str.maketrans("₀₁₂₃₄₅₆₇₈₉", "0123456789")))):
        ref, label, desc = KNOWN_THEOREMS[tname]
        formula = verse_formula(ref)
        lines.append(f"  {tname:4s} {label:12s}  {ref:25s}  {{ {', '.join(sorted(formula))} }}")

    lines.append(f"\n── SUMMARY ──")
    lines.append(f"  Theorem clusters (>=5 verses, >=3 types): {len(clusters)}")
    lines.append(f"  Total verses in clusters: {sum(len(v) for v in clusters.values())}")
    return "\n".join(lines)


if __name__ == "__main__":
    print(summary())
