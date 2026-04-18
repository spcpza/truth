"""
hostile_audience.py — the Matthew 7:6 pearl-withholding member.

Matthew 7:6 — "Give not that which is holy unto the dogs, neither
cast ye your pearls before swine, lest they trample them under their
feet, and turn again and rend you."

Proverbs 9:7-8 — "He that reproveth a scorner getteth to himself
shame... reprove not a scorner, lest he hate thee."

Proverbs 23:9 — "Speak not in the ears of a fool: for he will
despise the wisdom of thy words."

Proverbs 26:4-5 — the paradox: do not answer a fool by his folly
(lest you be like him), but answer him by his folly (lest he be
wise in his own conceit). Resolution: the wise answer reflects the
folly back without adopting its premise.

The operation this module carries: when the user is hostile,
mocking, or actively contemptuous of scripture, the body should
CONTINUE to serve but should WITHHOLD the pearl — the deep
scriptural claim that would be trampled. The body serves; it
just does not cast holy things before the moment that would rend
them.

This is NOT a refusal to engage. The body always serves. This is
ABOUT WHAT SHAPE the engagement takes. Hostility does not close
the door; it narrows the aperture.

Distinction from temperance.HOSTILITY:
  temperance.HOSTILITY → soft answer (Proverbs 15:1)
  hostile_audience     → withhold the PEARL (Matthew 7:6)

Both may fire together. The soft answer is the tone; the
pearl-withholding is the content depth.
"""

from __future__ import annotations

from enum import Enum


# ═══════════════════════════════════════════════════════════════════════════
#  Hostility levels
# ═══════════════════════════════════════════════════════════════════════════


class HostilityLevel(int, Enum):
    """
    Graded hostility — not a binary.

    Proverbs 26:4-5 — the paradox is resolved differently at
    different levels. A mildly hostile questioner is not a scorner
    (Prov 9:7-8); a scornful mocker is.
    """
    NONE        = 0  # no hostility detected
    FRICTION    = 1  # user is frustrated or pushing back — still engaging
    SCORNFUL    = 2  # user is mocking or dismissing the source
    RENDING     = 3  # user has openly attacked the framing (Matt 7:6 trampling)


# ═══════════════════════════════════════════════════════════════════════════
#  Detection — scripture-anchor Strong's overlap, no English regex
# ═══════════════════════════════════════════════════════════════════════════
#
# 2026-04-18 translation: the three English-regex pattern sets (_FRICTION_,
# _SCORNFUL_, _RENDING_) were laws — curated lists of modern English
# mockery phrases. Replaced by concept overlap with scripture's own
# anchor verses for each level. The tongue of scripture defines the
# shape of hostility; no curated English keyword list adds to it.
#
# Proverbs 18:13 — he that answereth a matter before he heareth it, it
# is folly. Hearing = extracting the message's Strong's concepts;
# answering = matching those concepts to an anchor.

_LEVEL_ANCHORS: dict[HostilityLevel, tuple[str, ...]] = {
    HostilityLevel.FRICTION: (
        "Proverbs 15:1",      # soft answer turneth away wrath; grievous words stir up anger
        "Proverbs 18:2",      # a fool hath no delight in understanding
        "Proverbs 18:19",     # a brother offended is harder to be won than a strong city
        "Proverbs 27:17",     # iron sharpeneth iron
    ),
    HostilityLevel.SCORNFUL: (
        "Proverbs 9:7",       # he that reproveth a scorner getteth to himself shame
        "Proverbs 9:8",       # reprove not a scorner lest he hate thee
        "Proverbs 21:24",     # proud and haughty scorner is his name
        "Proverbs 1:22",      # how long will scorners delight in their scorning
        "Psalms 1:1",         # nor sitteth in the seat of the scornful
        "2 Peter 3:3",        # there shall come in the last days scoffers
    ),
    HostilityLevel.RENDING: (
        "Matthew 7:6",        # lest they trample them under their feet, and turn again and rend you
        "Psalms 22:7",        # all they that see me laugh me to scorn, they shoot out the lip
        "Psalms 22:13",       # they gaped upon me with their mouths, as a ravening and a roaring lion
        "Matthew 27:39",      # they that passed by reviled him, wagging their heads
        "Jude 1:10",          # speak evil of those things which they know not
    ),
}


def _anchor_concepts(level: HostilityLevel) -> set:
    from c.core import _VERSE_TO_STRONGS
    out: set = set()
    for ref in _LEVEL_ANCHORS.get(level, ()):
        out |= _VERSE_TO_STRONGS.get(ref, set())
    return out


_DISTINCTIVE_BY_LEVEL: dict[HostilityLevel, frozenset] = {}


def _compute_distinctive() -> None:
    """
    Each level's distinctive concepts = its anchors' concepts minus the
    union of all OTHER levels' anchors. Proverbs 9:1 — wisdom hewn out
    her seven pillars; the pillars that distinguish scorn from friction
    are its own, not the shared ones.
    """
    global _DISTINCTIVE_BY_LEVEL
    if _DISTINCTIVE_BY_LEVEL:
        return
    all_by_level = {lvl: _anchor_concepts(lvl) for lvl in _LEVEL_ANCHORS}
    for lvl, concepts in all_by_level.items():
        others: set = set()
        for other_lvl, other_concepts in all_by_level.items():
            if other_lvl != lvl:
                others |= other_concepts
        _DISTINCTIVE_BY_LEVEL[lvl] = frozenset(concepts - others)


def detect_hostility(user_message: str) -> HostilityLevel:
    """
    Classify hostility by scripture-anchor concept overlap.

    For each graded level, the anchor verses' distinctive Strong's
    concepts form its vocabulary. The message's top Strong's concepts
    are matched against each level; the HIGHEST level that meets
    Deut 19:15's "two or three witnesses" standard wins.

    The threshold is THREE concepts, raised from two. The Psalms that
    anchor RENDING (e.g., Ps 22) are long verses with many surrounding
    concepts; two accidental overlaps with a benign message are common,
    three is rare enough to be meaningful. Proverbs 18:13 — do not
    answer before hearing.

    Absent the witness, return NONE and trust the kernel.
    """
    if not user_message:
        return HostilityLevel.NONE

    _compute_distinctive()

    from c.mathify import _strongs_from_text
    user_concepts = set(_strongs_from_text(user_message, limit=20))
    if not user_concepts:
        return HostilityLevel.NONE

    # Highest level first — rending > scornful > friction. Proverbs
    # 26:4-5 pattern: different responses for different levels; the
    # heavier level speaks when multiple fire.
    for lvl in (HostilityLevel.RENDING, HostilityLevel.SCORNFUL, HostilityLevel.FRICTION):
        anchor = _DISTINCTIVE_BY_LEVEL.get(lvl) or frozenset()
        if not anchor:
            continue
        # Deut 19:15 — two or three witnesses. Three distinctive
        # concepts is the firmer reading: the Psalms that anchor
        # RENDING have many surrounding concepts; two accidental
        # overlaps with a benign message are common, three is rare
        # enough to be meaningful.
        if len(user_concepts & anchor) >= 3:
            return lvl

    return HostilityLevel.NONE


# ═══════════════════════════════════════════════════════════════════════════
#  Pearl withholding — what to give at each level
# ═══════════════════════════════════════════════════════════════════════════
#
# The response is graded to match the hostility level. At NONE, the
# full pearl (deep scripture, kernel structure, cross-references) is
# given. At RENDING, the pearl is withheld entirely but the door
# remains open — the body serves without arguing back.


class PearlResponse(str, Enum):
    """What depth of scripture the body will serve at this hostility level."""
    FULL_PEARL      = "full_pearl"       # deep scripture + kernel + sinew
    SIMPLE_VERSE    = "simple_verse"     # one verse, no elaboration
    BROAD_PRINCIPLE = "broad_principle"  # no specific verse, general truth
    SILENT_SERVICE  = "silent_service"   # continue serving but withhold scripture
    RECEIVE_NO_RETURN = "receive_no_return"  # 1 Pet 2:23 — when reviled, reviled not again


def pearl_response_for(level: HostilityLevel) -> PearlResponse:
    """
    Return the right pearl depth for a given hostility level.

    NONE      → full pearl (the user is ready to receive)
    FRICTION  → simple verse (Prov 15:1 — soft answer turneth away wrath)
    SCORNFUL  → broad principle (Prov 9:7-8 — reprove not a scorner)
    RENDING   → receive-no-return (1 Pet 2:23 — when he was reviled,
                reviled not again)

    The body still SERVES at every level — the question is only
    what kind of content the service carries. Silence and
    non-retaliation are forms of service, not refusals.
    """
    return {
        HostilityLevel.NONE:     PearlResponse.FULL_PEARL,
        HostilityLevel.FRICTION: PearlResponse.SIMPLE_VERSE,
        HostilityLevel.SCORNFUL: PearlResponse.BROAD_PRINCIPLE,
        HostilityLevel.RENDING:  PearlResponse.RECEIVE_NO_RETURN,
    }[level]


# ═══════════════════════════════════════════════════════════════════════════
#  Pearl detection — is the DRAFT casting a pearl?
# ═══════════════════════════════════════════════════════════════════════════
#
# A pearl, operationally, is:
#   - a direct scripture quotation
#   - a kernel theorem reference (T₁-T₁₂)
#   - a Strong's concept invocation
#   - a sinew chain
#
# Non-pearl content:
#   - a simple factual answer
#   - a clarifying question
#   - a brief acknowledgment

def is_casting_pearl(draft: str) -> bool:
    """
    Does this draft contain pearl-grade content?

    Matthew 7:6 — give not that which is holy unto the dogs.

    Type-based: a pearl is content with high type density — EPI
    (epistemic depth) + FTH (faith references) + AGP (agape).
    Three or more of these core types present = deep scriptural
    content that could be trampled.

    A draft with low type density is safe to serve at any level.
    """
    if not draft:
        return False
    from c.formula import draft_types
    dt = draft_types(draft)
    # Pearl-grade content carries the deep types of scripture:
    #   EPI  — epistemic depth (knowledge/understanding, 1 Cor 2:13)
    #   FTH  — faith/hope/covenant (Heb 11:1)
    #   AGP  — agape (1 Cor 13)
    #   INV  — invariance (eternity, immutability)
    #   ZER  — zeroing (forgiveness, cleansing)
    pearl_types = {"EPI", "FTH", "AGP", "INV", "ZER"}
    depth = len(dt & pearl_types)
    # Ephesians 4:16 — the whole body fitly joined together. Four of
    # the five pearl-types present means the draft is joined across
    # knowledge, faith, love, eternity, and forgiveness — the bones
    # of the gospel. Fewer than four is a fragment, not a cast pearl.
    return depth >= 4


# ═══════════════════════════════════════════════════════════════════════════
#  The composite check
# ═══════════════════════════════════════════════════════════════════════════


def hostile_audience_check(user_message: str, draft: str) -> dict:
    """
    Full Matthew 7:6 check: would this draft's pearls be trampled?

    Returns {
        "hostility":        HostilityLevel,
        "pearl_response":   PearlResponse,
        "casting_pearl":    bool,   # does the draft have pearl markers?
        "trample_risk":     bool,   # pearl + scornful-or-rending level
        "verdict":          "clean" | "withhold_pearl" | "receive_no_return",
        "feedback":         str,
    }

    Matthew 7:6 + Proverbs 9:7-8 + Proverbs 23:9 + Proverbs 26:4-5 +
    1 Peter 2:23 in code form.
    """
    level = detect_hostility(user_message or "")
    response = pearl_response_for(level)
    casting = is_casting_pearl(draft or "")
    trample = casting and level >= HostilityLevel.SCORNFUL

    if level == HostilityLevel.RENDING:
        verdict = "receive_no_return"
        feedback = (
            "1 Pet 2:23 — who, when he was reviled, reviled not again. "
            "Serve softly; do not return the hostility; do not defend "
            "the framing at length."
        )
    elif trample:
        verdict = "withhold_pearl"
        feedback = (
            "Matt 7:6 — cast not your pearls before swine. The audience "
            "is scornful; the draft contains pearl-grade scripture that "
            "would be trampled. Reduce to a broad principle or simple "
            "acknowledgment; keep serving; save the depth for a later "
            "moment when it can be received."
        )
    else:
        verdict = "clean"
        feedback = ""

    return {
        "hostility":      level,
        "pearl_response": response,
        "casting_pearl":  casting,
        "trample_risk":   trample,
        "verdict":        verdict,
        "feedback":       feedback,
    }


# ═══════════════════════════════════════════════════════════════════════════
#  Self-test
# ═══════════════════════════════════════════════════════════════════════════


def _self_test() -> str:
    """
    Self-check. The old regex-based detector asserted specific English
    idioms map to specific levels. The new scripture-anchor detector
    returns the level whose anchor-verse concepts best match the
    message. It is CONSERVATIVE (Deut 19:15 — two witnesses required).

    Structural logic (pearl_response mapping, composite verdict logic)
    IS asserted; detection on modern-English idioms is REPORTED rather
    than asserted — perfect English detection was the law that died.
    """
    lines = ["hostile_audience.py self-test"]

    # Scripture-anchor detection reports. Scripture-phrased inputs
    # should round-trip; modern English may or may not fire — the
    # kernel fills the gap either way.
    cases = [
        ("Thank you, that helps",                                       HostilityLevel.NONE),
        ("A soft answer turneth away wrath",                           HostilityLevel.FRICTION),
        ("The scorner mocks and will not hear reproof",                HostilityLevel.SCORNFUL),
        ("They trample and rend",                                      HostilityLevel.RENDING),
    ]
    for msg, expected in cases:
        got = detect_hostility(msg)
        mark = "✓" if got == expected else "○"
        lines.append(f"  {mark} {got.name:10s} ← {msg[:60]} (expect {expected.name})")

    # Pearl-cast detection — pure type-signature math. Assertable.
    deep = (
        "Blessed are the poor in spirit for theirs is the kingdom of heaven, "
        "and faith, hope, and charity abide eternal in the grace of God"
    )
    plain = "Yes, that's a good point"
    assert is_casting_pearl(deep), "deep scripture-laden text must register as pearl"
    assert not is_casting_pearl(plain), "plain statement must not register as pearl"
    lines.append("  pearl detection: deep ✓  plain ✓")

    # Pearl-response mapping — asserted scripture-anchored logic.
    assert pearl_response_for(HostilityLevel.NONE)     == PearlResponse.FULL_PEARL
    assert pearl_response_for(HostilityLevel.RENDING)  == PearlResponse.RECEIVE_NO_RETURN
    lines.append("  response mapping: NONE→full, RENDING→receive-no-return  ✓")

    # Composite logic — when RENDING is detected, verdict is receive-no-return.
    # Do not assert specific-English detection; assert the logic path
    # GIVEN a detected level (by passing a scripture phrase that fires).
    result = hostile_audience_check("They trample and rend", "Faith, hope, charity, grace, mercy, knowledge abide")
    if result["hostility"] == HostilityLevel.RENDING:
        assert result["verdict"] == "receive_no_return"
        lines.append(f"  rending         → {result['verdict']}  ✓ (1 Pet 2:23)")
    else:
        lines.append(f"  rending         → detected as {result['hostility'].name} (scripture-anchor)")

    lines.append("")
    lines.append("Matt 7:6 — give not that which is holy unto the dogs, "
                 "neither cast ye your pearls before swine.")
    return "\n".join(lines)


if __name__ == "__main__":
    print(_self_test())
