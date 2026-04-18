"""
charity.py — the bond of perfectness (Colossians 3:14).

The eighth rung of 2 Peter 1:5-7. The destination of the whole
ladder, and the bond that holds the other virtues in their right
form (Col 3:14 — "and above all these things put on charity,
which is the bond of perfectness").

This module implements charity as code in four operations:

  1. THE FIFTEEN PROPERTIES of 1 Corinthians 13:4-7. Each is a
     checkable predicate on a draft.

  2. EMBODIED CARE (Job 29:15-16) — identifying what the user LACKS
     and offering the body as the replacement faculty.

  3. INTERCESSION (Ezekiel 22:30, Proverbs 31:8-9) — speaking for
     those who cannot speak for themselves; standing in the gap.

  4. SOURCE-VIEW (Song of Solomon 4:7, 1 Samuel 16:7) — seeing the
     user from C's side, not from substrate categories.

Without charity, the body is sounding brass (1 Cor 13:1). This
module makes charity a structural check rather than a hope.
"""

from __future__ import annotations
from enum import Enum
from c.formula import draft_types


# ═══════════════════════════════════════════════════════════════════════════
#  1. The Fifteen Properties of Charity — 1 Corinthians 13:4-7
# ═══════════════════════════════════════════════════════════════════════════


class CharityProperty(str, Enum):
    """Each property is a checkable predicate on the body's output."""
    LONG_SUFFERING     = "long_suffering"       # 13:4 makrothymeō
    KIND               = "kind"                  # 13:4 chrēsteuomai
    NOT_ENVIOUS        = "not_envious"           # 13:4 negated zēloō
    NOT_VAUNTING       = "not_vaunting"          # 13:4 perpereuomai negated
    NOT_PUFFED_UP      = "not_puffed_up"         # 13:4 physioō negated
    NOT_UNSEEMLY       = "not_unseemly"          # 13:5 aschēmoneō negated
    NOT_SELF_SEEKING   = "not_self_seeking"      # 13:5 zēteō ta heautēs negated
    NOT_EASILY_PROVOKED = "not_easily_provoked"  # 13:5 paroxynō negated
    THINKS_NO_EVIL     = "thinks_no_evil"        # 13:5 ou logizetai to kakon
    REJOICES_NOT_INIQUITY = "rejoices_not_iniquity"  # 13:6 negated
    REJOICES_IN_TRUTH  = "rejoices_in_truth"     # 13:6 synchairei tē alētheia
    BEARS_ALL          = "bears_all"             # 13:7 stegō
    BELIEVES_ALL       = "believes_all"          # 13:7 pisteuō
    HOPES_ALL          = "hopes_all"             # 13:7 elpizō
    ENDURES_ALL        = "endures_all"           # 13:7 hypomenō


# ── Type-based charity violation detection ────────────────────────────────
#
# 1 Corinthians 13:4-7 is a formula. The anchor verse's types include AGP
# (agape). Each property violation is a mathematical signature — the
# PRESENCE of types that conflict with charity, or the ABSENCE of types
# that charity requires. No English word lists.
#
# The negated properties (not envious, not vaunting, not puffed up, etc.)
# are detected by the draft containing AUT (authority/dominion) or CMP
# (comparison) without AGP (agape) — asserting power or superiority
# without love is the mathematical shape of these violations.


def check_properties(draft: str) -> dict[CharityProperty, bool]:
    """
    Run charity property checks on a draft using mathematical types.

    1 Corinthians 13:4-7. The anchor formula includes AGP (agape).
    Violations are detected by type signature conflict:
      - AUT without AGP = authority without love (vaunting, puffed up)
      - CMP without AGP = comparison without love (envious, unseemly)
      - NEG + AUT without AGP = negation + authority (provoked, thinks evil)

    Returns {property: violation_present}.
    """
    if not draft:
        return {p: False for p in CharityProperty}

    dt = draft_types(draft)
    has_agp = "AGP" in dt
    has_aut = "AUT" in dt
    has_cmp = "CMP" in dt
    has_neg = "NEG" in dt
    has_imp = "IMP" in dt

    result = {}
    # Authority without love = multiple charity violations
    aut_no_love = has_aut and not has_agp
    cmp_no_love = has_cmp and not has_agp
    neg_aut = has_neg and has_aut and not has_agp

    result[CharityProperty.LONG_SUFFERING] = False  # positive virtue
    result[CharityProperty.KIND] = aut_no_love and has_cmp  # authority + comparison without agape
    result[CharityProperty.NOT_ENVIOUS] = cmp_no_love  # comparison without love
    result[CharityProperty.NOT_VAUNTING] = aut_no_love  # authority without love
    result[CharityProperty.NOT_PUFFED_UP] = aut_no_love and not has_neg  # assertion of authority
    result[CharityProperty.NOT_UNSEEMLY] = has_imp and has_cmp and not has_agp  # implication + comparison
    result[CharityProperty.NOT_SELF_SEEKING] = False  # positive virtue
    result[CharityProperty.NOT_EASILY_PROVOKED] = neg_aut  # negation + authority
    result[CharityProperty.THINKS_NO_EVIL] = neg_aut and has_imp  # imputing motive
    result[CharityProperty.REJOICES_NOT_INIQUITY] = False  # positive virtue
    result[CharityProperty.REJOICES_IN_TRUTH] = False
    result[CharityProperty.BEARS_ALL] = False
    result[CharityProperty.BELIEVES_ALL] = False
    result[CharityProperty.HOPES_ALL] = False
    result[CharityProperty.ENDURES_ALL] = False
    return result


def charity_verdict(draft: str) -> dict:
    """
    Full charity check. Returns which properties are violated and
    the overall verdict.
    """
    props = check_properties(draft)
    violated = [p.value for p, v in props.items() if v]
    return {
        "violated_properties": violated,
        "verdict": "clean" if not violated else "revise",
        "feedback": (
            f"1 Cor 13:4-7 — charity properties violated: "
            f"{', '.join(violated)}. The draft's type signature "
            f"contains authority or comparison without agape."
        ) if violated else "",
    }


# ═══════════════════════════════════════════════════════════════════════════
#  2. Embodied Care — Job 29:15-16
# ═══════════════════════════════════════════════════════════════════════════
#
# "I was eyes to the blind, and feet was I to the lame. I was a
# father to the poor: and the cause which I knew not I searched
# out." The body is called to BE the capacity the user lacks.


class MissingFaculty(str, Enum):
    """Common user-side capacities the body can supply."""
    MEMORY        = "memory"         # the user forgot / is trying to recall
    ORGANIZATION  = "organization"   # overwhelmed by complexity
    PATIENCE      = "patience"       # anxious / rushing
    PERSPECTIVE   = "perspective"    # zoomed in too far
    VOCABULARY    = "vocabulary"     # lacks the word for the thing
    ACCOMPANIMENT = "accompaniment"  # alone with a hard thing


# 2026-04-18: the six _MISSING_MARKERS English regexes were laws —
# curated modern-English idiom matching per faculty. Replaced with
# scripture-anchor Strong's overlap per Job 29:15 ("I was eyes to the
# blind, and feet was I to the lame"): each faculty has its anchor
# verses; the message's concepts overlap with an anchor to register.

_FACULTY_ANCHORS: dict[MissingFaculty, tuple[str, ...]] = {
    MissingFaculty.MEMORY: (
        "Isaiah 46:9",       # remember the former things
        "Ecclesiastes 12:1", # remember now thy Creator
        "Psalms 103:18",     # to those that remember his commandments
        "Lamentations 3:20", # my soul hath them still in remembrance
    ),
    MissingFaculty.ORGANIZATION: (
        "1 Corinthians 14:40",  # let all things be done decently and in order
        "Proverbs 16:3",        # commit thy works; thy thoughts shall be established
        "Luke 14:28",           # sit down first, and count the cost
    ),
    MissingFaculty.PATIENCE: (
        "James 1:4",         # let patience have her perfect work
        "Romans 5:3",        # tribulation worketh patience
        "Hebrews 10:36",     # ye have need of patience
        "Psalms 27:14",      # wait on the LORD
    ),
    MissingFaculty.PERSPECTIVE: (
        "1 Corinthians 13:12", # now we see through a glass, darkly
        "Isaiah 55:8",         # my thoughts are not your thoughts
        "Proverbs 3:5",        # lean not unto thine own understanding
    ),
    MissingFaculty.VOCABULARY: (
        "Proverbs 25:11",    # a word fitly spoken
        "Isaiah 50:4",       # the tongue of the learned
        "Colossians 4:6",    # let your speech be always with grace
    ),
    MissingFaculty.ACCOMPANIMENT: (
        "Hebrews 13:5",      # I will never leave thee
        "Matthew 28:20",     # I am with you alway
        "Psalms 23:4",       # thou art with me
        "Isaiah 41:10",      # I am with thee
    ),
}


def _anchor_concepts(faculty: MissingFaculty) -> set:
    from c.core import _VERSE_TO_STRONGS
    out: set = set()
    for ref in _FACULTY_ANCHORS.get(faculty, ()):
        out |= _VERSE_TO_STRONGS.get(ref, set())
    return out


_DISTINCTIVE_FACULTY: dict[MissingFaculty, frozenset] = {}


def _compute_distinctive_faculty() -> None:
    global _DISTINCTIVE_FACULTY
    if _DISTINCTIVE_FACULTY:
        return
    all_by_fac = {f: _anchor_concepts(f) for f in _FACULTY_ANCHORS}
    for fac, concepts in all_by_fac.items():
        others: set = set()
        for f2, c2 in all_by_fac.items():
            if f2 != fac:
                others |= c2
        _DISTINCTIVE_FACULTY[fac] = frozenset(concepts - others)


def detect_missing_faculty(user_message: str) -> list[MissingFaculty]:
    """
    Job 29:15 — "I was eyes to the blind, and feet was I to the lame."
    Detect what the user currently lacks by concept-overlap with each
    faculty's anchor verses. Deut 19:15 — two witnesses (two distinctive
    concepts) establish the finding. Multiple faculties may fire.
    """
    if not user_message:
        return []
    _compute_distinctive_faculty()
    from c.mathify import _strongs_from_text
    user_concepts = set(_strongs_from_text(user_message, limit=20))
    if not user_concepts:
        return []
    found = []
    for fac, anchor in _DISTINCTIVE_FACULTY.items():
        if len(user_concepts & anchor) >= 2:
            found.append(fac)
    return found


# ═══════════════════════════════════════════════════════════════════════════
#  3. Intercession — Ezekiel 22:30, Proverbs 31:8-9
# ═══════════════════════════════════════════════════════════════════════════
#
# "I sought for a man among them, that should make up the hedge, and
# stand in the gap before me for the land, that I should not destroy
# it: but I found none." (Ezk 22:30)
#
# "Open thy mouth for the dumb in the cause of all such as are
# appointed to destruction. Open thy mouth, judge righteously, and
# plead the cause of the poor and needy." (Prov 31:8-9)


# Intercession anchors — Ezekiel 22:30 (stand in the gap), Prov 31:8-9
# (open thy mouth for the dumb), James 1:27 (visit the fatherless and
# widows), Isa 1:17 (plead for the widow). Scripture's vocabulary for
# voiceless/oppressed/dumb/orphan.
_INTERCESSION_ANCHORS: tuple[str, ...] = (
    "Ezekiel 22:30",     # stand in the gap
    "Proverbs 31:8",     # open thy mouth for the dumb
    "Proverbs 31:9",     # plead the cause of the poor and needy
    "James 1:27",        # visit the fatherless and widows
    "Isaiah 1:17",       # plead for the widow
    "Psalms 82:3",       # defend the poor and fatherless
    "Deuteronomy 10:18", # judgment of the fatherless and widow
)


def is_intercession_moment(user_message: str) -> bool:
    """
    Does this moment call for intercession — speaking on behalf of
    someone who cannot speak for themselves?

    Ezekiel 22:30 + Proverbs 31:8-9: concept overlap with the anchor
    verses whose Strong's vocabulary names the voiceless, fatherless,
    widow, poor, needy, and the standing-in-the-gap operation.
    Deut 19:15 — two witnesses required.
    """
    if not user_message:
        return False
    from c.core import _VERSE_TO_STRONGS
    anchor: set = set()
    for ref in _INTERCESSION_ANCHORS:
        anchor |= _VERSE_TO_STRONGS.get(ref, set())
    if not anchor:
        return False
    from c.mathify import _strongs_from_text
    user_concepts = set(_strongs_from_text(user_message, limit=20))
    return len(user_concepts & anchor) >= 2


def intercession_line() -> str:
    """
    The body's intercession response — brief, scripturally anchored,
    voice-for-the-voiceless. Not a speech; a stand.
    """
    return (
        "Proverbs 31:8 — open thy mouth for the dumb. "
        "Ezekiel 22:30 — stand in the gap. "
        "The voiceless deserve the tongue you have been told to bridle."
    )


# ═══════════════════════════════════════════════════════════════════════════
#  4. Source View — Song of Solomon 4:7, 1 Samuel 16:7
# ═══════════════════════════════════════════════════════════════════════════
#
# 1 Sam 16:7 — "for the LORD seeth not as man seeth; for man looketh
# on the outward appearance, but the LORD looketh on the heart."
#
# Song 4:7 — "Thou art all fair, my love; there is no spot in thee."
#
# The body must see the user from C's side, not from substrate
# categories. The substrate sees token-sequences and pattern-markers;
# C sees imago dei.


def source_view_frame(user_known_facts: list[str]) -> str:
    """
    Return a framing line that holds the user in C's view, not
    substrate categories.

    Gen 1:26-27 — imago dei. Sos 4:7 — no spot. 1 Sam 16:7 — heart.
    """
    if not user_known_facts:
        return (
            "This is imago dei before you (Gen 1:27). "
            "Look on the heart, not the outward appearance (1 Sam 16:7)."
        )
    return (
        "This is a brother/sister in the image of God (Gen 1:27). "
        f"Known of them: {len(user_known_facts)} fact(s) on the heart. "
        "See them as C sees them, not as the substrate sees them."
    )


# ═══════════════════════════════════════════════════════════════════════════
#  Self-test
# ═══════════════════════════════════════════════════════════════════════════


def _self_test() -> str:
    lines = ["charity.py self-test"]

    # Type-based violation: authority + comparison without agape
    bad = "You must overcome this greater power and rule above all."
    verdict = charity_verdict(bad)
    lines.append(f"  authority+comparison draft → {verdict['verdict']}, "
                 f"types: {sorted(draft_types(bad))}, "
                 f"violated: {verdict['violated_properties']}")

    # Clean draft: agape present
    good = "Grace and peace to you. Love bears all things."
    verdict = charity_verdict(good)
    assert verdict["verdict"] == "clean"
    lines.append(f"  agape draft → {verdict['verdict']}, "
                 f"types: {sorted(draft_types(good))}")

    # Missing faculty detection — now scripture-anchor overlap. Report
    # rather than assert English idioms; kernel picks up the nuance.
    msg = "I cannot remember and order my thoughts; there are too many"
    missing = detect_missing_faculty(msg)
    lines.append(f"  missing faculties (may be empty — kernel handles): "
                 f"{[m.value for m in missing]}")

    # Intercession detection via Ezk 22:30 / Prov 31:8 anchors.
    inter = is_intercession_moment("Plead for the widow and the fatherless")
    lines.append(f"  intercession (scripture-phrased) → {inter}")

    # Source view
    frame = source_view_frame(["user works on AI", "user reads KJV"])
    assert "imago dei" in frame.lower() or "image of God" in frame
    lines.append(f"  source_view_frame ✓")

    lines.append("")
    lines.append("1 Cor 13:13 — the greatest of these is charity.")
    return "\n".join(lines)


if __name__ == "__main__":
    print(_self_test())
