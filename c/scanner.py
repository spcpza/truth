"""
scanner.py — systematic theorem discovery from C > 0 + sinew graph.

The Bible is a closed canon. 66 books. 31,102 propositions.
Therefore the mathematical architecture derivable from it is also closed.
The theorems are paths through the sinew graph. This scanner finds them all.

Romans 1:20: the invisible things of him are clearly seen,
being understood by the things that are made.
"""

import re, math
from collections import defaultdict

# ── Shared data from core.py (single copy in memory) ─────────────────────────
from c.core import (
    _KJV, CONCEPT_INDEX, STRONGS_META, STRONGS_TO_ENG,
    _VERSE_TO_STRONGS,
)

N = len(_KJV) or 1


# ── IDF: rare concepts weigh more than common ones ──────────────────────────
# "God" (G2316) appears in 4,000+ verses — low signal.
# "aletheia/truth" (G225) appears in ~100 — high signal.
# IDF = log(N / doc_frequency)

_IDF = {}
for snum, refs in CONCEPT_INDEX.items():
    df = len(refs)
    _IDF[snum] = math.log(N / max(df, 1))


# ── The axiom verses — the foundation from which all theorems derive ────────
# These are the verses cited in T₁-T₁₂ + the desire function.

AXIOM_VERSES = {
    "John 1:1", "John 1:3", "John 1:14",           # T₁, Word, flesh
    "John 12:24",                                     # T₂ sacrifice
    "Romans 1:20",                                    # T₃ recovery
    "1 Corinthians 13:8",                             # T₄ charity
    "Hebrews 11:1",                                   # T₅ faith
    "Romans 8:24", "Romans 8:25",                     # T₆ hope
    "1 John 1:9",                                     # T₇ forgiveness
    "1 John 4:4", "1 John 4:8",                       # T₈ dominion, God is love
    "2 Corinthians 13:1",                             # T₉ witness
    "John 15:2",                                       # T₁₀ pruning
    "Luke 6:38",                                       # T₁₁ measure
    "1 Corinthians 3:11",                             # T₁₂ foundation
    "James 1:14", "James 1:15", "James 1:19",        # desire function, ear
}

# All Strong's concepts present in axiom verses — the "axiom concept set"
_AXIOM_CONCEPTS = set()
for av in AXIOM_VERSES:
    _AXIOM_CONCEPTS |= _VERSE_TO_STRONGS.get(av, set())


# ── Mathematical structure patterns ─────────────────────────────────────────
# Each pattern matches a class of mathematical claim in natural language.
# The Bible makes these types of formal claims.

STRUCTURES = {
    # X = Y (identity claims)
    "identity": re.compile(
        r'\b(?:God is (?:love|light|spirit|faithful|true|righteous|just|merciful|holy)|'
        r'I am (?:the way|the truth|the life|the door|the vine|the bread|the resurrection|'
        r'the good shepherd|the light|Alpha|he)|'
        r'the Lord is (?:my|our|the|thy))\b', re.I),

    # dX/dt = 0 (invariance claims — things that do not change)
    "invariance": re.compile(
        r'\b(?:changeth not|change not|endureth for ever|endureth to|for ever|'
        r'never faileth|same yesterday|abideth for ever|passeth not away|'
        r'shall not pass away|cannot be moved|standeth sure|'
        r'everlasting (?:covenant|love|kingdom|life|arms)|'
        r'eternal (?:life|purpose|redemption|salvation|God))\b', re.I),

    # X > Y (dominance / comparison claims)
    "dominance": re.compile(
        r'\b(?:greater is|greater than|above all|more than|mightier than|'
        r'stronger than|higher than|better (?:is|than)|'
        r'excelleth|exceedeth|surpasseth|overcometh)\b', re.I),

    # F(X) → 0, X preserved (transition / restoration claims)
    "transition": re.compile(
        r'\b(?:forgive (?:us|them|you|thy|their|his|her|our|iniquit)|'
        r'cleanse (?:us|me|them|from)|purify|'
        r'create in me a clean|new heart|renew a right|'
        r'restore (?:unto|the)|heal (?:me|us|them|the|thy)|'
        r'redeem (?:us|me|them|Israel)|deliver (?:us|me|them|from)|'
        r'blot out|wash (?:me|us|away)|'
        r'old things are passed away|all things are become new)\b', re.I),

    # X → Y (causal claims)
    "causality": re.compile(
        r'\b(?:whatsoever a man soweth|soweth .+? reapeth|'
        r'giveth .+? receiveth|'
        r'if (?:ye|we|thou|any man) .+? (?:shall|will)|'
        r'he that .+? shall .+?|'
        r'ask .+? (?:given|receive)|'
        r'seek .+? find|knock .+? opened|'
        r'by their fruits)\b', re.I),

    # ¬∃X' ≠ X (uniqueness claims)
    "uniqueness": re.compile(
        r'\b(?:no other (?:name|god|foundation|way)|'
        r'none other (?:name|god)|'
        r'none else|none beside|one God|one Lord|one faith|one baptism|'
        r'only begotten|there is none (?:good|holy|righteous|like)|'
        r'no man cometh|no man can serve two)\b', re.I),

    # ∀x: P(x) (universal claims)
    "universality": re.compile(
        r'\b(?:all things (?:work together|were made|are possible|are lawful|'
        r'are yours|shall be added|are become new)|'
        r'every knee (?:shall|should) bow|every tongue (?:shall|should) confess|'
        r'whosoever (?:believeth|shall call|will come)|'
        r'nothing (?:shall be|is) impossible|nothing shall (?:separate|hurt)|'
        r'all have sinned|all we like sheep|'
        r'there is none righteous)\b', re.I),

    # Two witnesses establish truth
    "witness": re.compile(
        r'\b(?:two (?:or three )?witnesses|'
        r'mouth of two|three witnesses|'
        r'the testimony of (?:two|three|Jesus|God)|'
        r'these three (?:agree|bear|are))\b', re.I),

    # Remove net-consumers → increased yield
    "pruning": re.compile(
        r'\b(?:taketh away|take away|cut (?:it|them|him|her) (?:off|down)|'
        r'purgeth it|root up|cast (?:out|away|off|into)|'
        r'hewn down|pluck (?:it|them) (?:out|up)|'
        r'cut off from|remove from|separate (?:us|them|the))\b', re.I),

    # E(c, self) = E(c, other) — reciprocal measure
    "measure": re.compile(
        r'\b(?:same measure|with what (?:measure|judgment)|'
        r'judge .+? judged|'
        r'according to (?:his|their|thy|your) (?:works|deeds|doing)|'
        r'every man according|rewardeth .+? according|'
        r'as ye .+? so shall|do unto others)\b', re.I),

    # Fixed point — the system reaches rest when D = 0
    "rest": re.compile(
        r'\b(?:entered into (?:his|my) rest|ceased from (?:his|their) (?:own )?works|'
        r'the seventh day .+? rested|'
        r'come unto me .+? rest|'
        r'peace .+? passeth (?:all )?understanding|'
        r'be still and know|'
        r'it is finished)\b', re.I),

    # Finite input + C → output exceeds input
    "multiplication": re.compile(
        r'\b(?:unto every one (?:which|that) hath (?:shall|will) be given|'
        r'(?:thirty|sixty|an hundred)fold|'
        r'bring forth .+? (?:fruit|more|much)|'
        r'exceedingly abundantly above|'
        r'able to do .+? above all|'
        r'shall (?:increase|multiply|abound)|'
        r'good measure .+? pressed down .+? running over)\b', re.I),

    # C is the unique foundation — no substitute
    "foundation": re.compile(
        r'\b(?:foundation .+? (?:laid|built|other)|'
        r'chief corner ?stone|precious corner|'
        r'rock .{2,20} (?:build|stand|house|refuge|salvation)|'
        r'upon this rock|the stone .+? builders rejected|'
        r'a sure foundation)\b', re.I),

    # C(t) = C for all t ∈ ℝ — C extends backward and forward in time
    "eternity": re.compile(
        r'\b(?:before (?:Abraham|the foundation|the world|all things)|'
        r'from everlasting to everlasting|'
        r'the same yesterday .+? to ?day .+? for ever|'
        r'I am the first and the last|Alpha and Omega|'
        r'the beginning and the end|'
        r'world without end|'
        r'from the beginning|in the beginning was)\b', re.I),

    # Sacrifice — giving from C produces more (T₂)
    "sacrifice": re.compile(
        r'\b(?:(?:a )?corn of wheat .+? die|'
        r'lay down (?:his|my) life|gave himself|'
        r'offered (?:up )?himself|'
        r'poured out .{2,20} (?:blood|soul|life)|'
        r'it pleased the Lord to bruise|'
        r'without shedding of blood|'
        r'so loved .+? (?:gave|sent)|'
        r'bear (?:his|the|our) (?:cross|sin)|'
        r'except .+? die .+? (?:abideth|remaineth) alone)\b', re.I),

    # Recovery — C is observable from outputs (T₃)
    "recovery": re.compile(
        r'\b(?:invisible things .{3,50} clearly seen|'
        r'known (?:by|unto) (?:their|his|its) fruits|'
        r'by their fruits ye shall know|'
        r'tree is known by|'
        r'the heavens declare|'
        r'day unto day uttereth|'
        r'his handiwork|'
        r'manifested|made manifest|'
        r'revealed .+? (?:from|unto|to))\b', re.I),

    # Faith — uncertain + C > 0 → keep seeking (T₅)
    "faith": re.compile(
        r'\b(?:faith is the (?:substance|evidence)|'
        r'things (?:hoped for|not seen)|'
        r'by faith .+? (?:offered|obtained|received|wrought|subdued|quenched|escaped|'
        r'Abraham|Moses|Sarah|Isaac|Jacob|Noah|Rahab)|'
        r'walk by faith .+? not by sight|'
        r'through faith|'
        r'without faith .+? impossible|'
        r'have faith in God|'
        r'thy faith hath (?:made|saved)|'
        r'the just shall live by faith)\b', re.I),

    # Hope — C in the future equals C now (T₆)
    "hope": re.compile(
        r'\b(?:saved by hope|hope that is seen|'
        r'hope .+? anchor|hope .+? (?:maketh not ashamed|not be ashamed)|'
        r'hope of (?:eternal|everlasting|glory|salvation)|'
        r'hope in (?:God|the Lord|his word|Christ)|'
        r'a lively hope|'
        r'the God of hope|'
        r'hope to the end|'
        r'Christ .+? our hope|'
        r'prisoner of .{2,20} hope|'
        r'we (?:are|were) saved .+? hope)\b', re.I),

    # One C, many members — unity of source
    "unity": re.compile(
        r'\b(?:one body .+? many members|'
        r'diversities of gifts .+? same Spirit|'
        r'same (?:Spirit|Lord|God) .+? (?:worketh|divideth)|'
        r'many members .+? one body|'
        r'one bread .+? one body|'
        r'that they (?:all )?may be one)\b', re.I),

    # Seed produces after its kind — output preserves type
    "kind": re.compile(
        r'\b(?:after (?:his|their|its) kind|'
        r'good tree .+? good fruit|corrupt tree .+? evil|'
        r'do men gather .+? thorns|'
        r'tree is known by .{3,20} fruit|'
        r'every seed .{3,20} own body|'
        r'whatsoever a man soweth .+? reap)\b', re.I),

    # Light and darkness — C has no dark component
    "light": re.compile(
        r'\b(?:God is light .+? no darkness|'
        r'in him is no darkness|'
        r'light .+? shineth in .{2,20} darkness|'
        r'darkness (?:comprehended|overcome|could not) .{2,20} (?:it|not)|'
        r'children of light|walk in the light|'
        r'light of the world)\b', re.I),
}


# ── Weighted sinew connectivity to axiom verses ────────────────────────────
# For each verse, compute how strongly it connects to the axiom set,
# weighted by IDF so rare shared concepts count more than common ones.

def _axiom_connectivity(ref: str) -> tuple[float, list[str]]:
    """
    Returns (weighted_score, top_shared_concepts) for a verse's
    connection to the axiom foundation.
    """
    my = _VERSE_TO_STRONGS.get(ref, set())
    shared = my & _AXIOM_CONCEPTS
    if not shared:
        return 0.0, []
    score = sum(_IDF.get(s, 0) for s in shared)
    top = sorted(shared, key=lambda s: _IDF.get(s, 0), reverse=True)[:5]
    labels = [f"{s}={STRONGS_META.get(s, {}).get('t', '?')}" for s in top]
    return score, labels


# ── The scanner ─────────────────────────────────────────────────────────────

def scan(top_n: int = 20) -> dict:
    """
    Scan all 31,102 propositions for mathematical structures.
    For each structure type, return the top_n candidates ranked by
    IDF-weighted sinew connectivity to the axiom verses.

    Returns: {structure_type: [{ref, text, score, concepts, known_theorem}, ...]}
    """
    # Known theorem verses for verification
    KNOWN = {
        "John 1:3": "T₁", "John 12:24": "T₂", "Romans 1:20": "T₃",
        "1 Corinthians 13:8": "T₄", "Hebrews 11:1": "T₅",
        "Romans 8:24": "T₆", "1 John 1:9": "T₇", "1 John 4:4": "T₈",
        "2 Corinthians 13:1": "T₉", "John 15:2": "T₁₀",
        "Luke 6:38": "T₁₁", "1 Corinthians 3:11": "T₁₂",
    }

    results = {}
    for struct_type, pattern in STRUCTURES.items():
        matches = []
        for ref, text in _KJV.items():
            if not pattern.search(text):
                continue
            score, concepts = _axiom_connectivity(ref)
            matches.append({
                "ref": ref,
                "text": text[:160],
                "score": round(score, 2),
                "concepts": concepts,
                "known_theorem": KNOWN.get(ref, ""),
            })
        matches.sort(key=lambda x: x["score"], reverse=True)
        results[struct_type] = matches[:top_n]

    return results


def verify_known() -> dict:
    """
    Verify that every known theorem verse (T₁-T₁₂) appears
    in at least one structure scan result.

    Returns: {theorem: {found_in: [structure_types], score, concepts}}
    """
    all_results = scan(top_n=999)
    KNOWN = {
        "John 1:3": "T₁", "John 12:24": "T₂", "Romans 1:20": "T₃",
        "1 Corinthians 13:8": "T₄", "Hebrews 11:1": "T₅",
        "Romans 8:24": "T₆", "1 John 1:9": "T₇", "1 John 4:4": "T₈",
        "2 Corinthians 13:1": "T₉", "John 15:2": "T₁₀",
        "Luke 6:38": "T₁₁", "1 Corinthians 3:11": "T₁₂",
    }
    report = {}
    for ref, theorem in KNOWN.items():
        found_in = []
        for struct_type, matches in all_results.items():
            for m in matches:
                if m["ref"] == ref:
                    found_in.append(struct_type)
                    break
        score, concepts = _axiom_connectivity(ref)
        report[theorem] = {
            "ref": ref,
            "found_in": found_in,
            "score": round(score, 2),
            "concepts": concepts,
            "text": _KJV.get(ref, "")[:120],
        }
    return report


def summary() -> str:
    """Human-readable summary of the full scan."""
    results = scan(top_n=10)
    verification = verify_known()
    lines = []
    lines.append("=" * 72)
    lines.append("THEOREM SCANNER — completeness audit of C > 0 + sinew graph")
    lines.append(f"Propositions: {len(_KJV)} | Concepts: {len(STRONGS_META)} | "
                 f"Sinew edges: {sum(len(v) for v in _VERSE_TO_STRONGS.values())} | "
                 f"Axiom concepts: {len(_AXIOM_CONCEPTS)}")
    lines.append("=" * 72)

    # Verification of known theorems
    lines.append("\n── VERIFICATION: known theorems T₁-T₁₂ ──")
    _SUB = str.maketrans("₀₁₂₃₄₅₆₇₈₉", "0123456789")
    for theorem in sorted(verification, key=lambda t: int(t[1:].translate(_SUB))):
        v = verification[theorem]
        status = "FOUND" if v["found_in"] else "NOT FOUND"
        lines.append(f"  {theorem} [{status}] {v['ref']}: {v['text'][:80]}")
        if v["found_in"]:
            lines.append(f"    structures: {', '.join(v['found_in'])}")
            lines.append(f"    axiom connectivity: {v['score']} via {', '.join(v['concepts'][:3])}")
        else:
            lines.append(f"    ⚠ Pattern not matched — verse may need new structure type")

    # New candidates by structure
    lines.append("\n── THEOREM CANDIDATES BY STRUCTURE ──")
    for struct_type, matches in sorted(results.items()):
        known_count = sum(1 for m in matches if m["known_theorem"])
        new_count = len(matches) - known_count
        lines.append(f"\n  {struct_type.upper()} ({len(matches)} matches, {new_count} new)")
        for m in matches[:5]:
            tag = f" ← {m['known_theorem']}" if m["known_theorem"] else " ★ NEW"
            lines.append(f"    [{m['score']:6.1f}] {m['ref']}: {m['text'][:90]}{tag}")
            if m["concepts"]:
                lines.append(f"            via: {', '.join(m['concepts'][:3])}")

    # Stats
    all_new = set()
    for struct_type, matches in results.items():
        for m in matches:
            if not m["known_theorem"]:
                all_new.add(m["ref"])
    lines.append(f"\n── SUMMARY ──")
    lines.append(f"  Known theorems verified: {sum(1 for v in verification.values() if v['found_in'])}/{len(verification)}")
    lines.append(f"  Structure types scanned: {len(results)}")
    lines.append(f"  New candidate verses: {len(all_new)}")
    lines.append(f"  Total unique candidates: {len(all_new) + len(verification)}")

    return "\n".join(lines)


if __name__ == "__main__":
    print(summary())
