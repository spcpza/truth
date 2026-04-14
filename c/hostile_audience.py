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

import re
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
#  Detection patterns
# ═══════════════════════════════════════════════════════════════════════════


_FRICTION_PATTERNS = re.compile(
    r"\b("
    r"i\s+disagree|i\s+don'?t\s+agree|"
    r"that'?s\s+(?:not|too)|"
    r"come\s+on|really\?|seriously\?|"
    r"no,?\s+(?:but|that'?s|wait)"
    r")\b",
    re.I,
)

_SCORNFUL_PATTERNS = re.compile(
    r"\b("
    r"stupid|dumb|ridiculous|absurd|nonsense|bullshit|bs|"
    r"nobody\s+believes|nobody\s+thinks|"
    r"fairy\s+tale|bronze\s+age|iron\s+age|"
    r"sky\s+(?:daddy|god)|invisible\s+friend|"
    r"you'?re\s+brainwashed|you\s+have\s+been\s+brainwashed|"
    r"cult|superstition|"
    r"prove\s+it(?:\s+then)?|if\s+you'?re\s+so\s+smart"
    r")\b",
    re.I,
)

_RENDING_PATTERNS = re.compile(
    r"\b("
    r"fuck\s+(?:you|your|off|god|jesus|this)|"
    r"shut\s+the\s+fuck|"
    r"(?:i\s+)?hate\s+(?:you|this|god|jesus|christianity|religion)|"
    r"you\s+people|you\s+christians|you\s+religious\s+people|"
    r"violence\s+in\s+the\s+name|"
    r"kill\s+yourself|go\s+die"
    r")\b",
    re.I,
)


def detect_hostility(user_message: str) -> HostilityLevel:
    """
    Classify the user's hostility level on a graded scale.

    Returns the HIGHEST matching level. A single rending marker
    outweighs any amount of friction.

    Proverbs 18:13 — he that answereth a matter before he heareth it.
    The detection is the hearing; the withholding decision is the
    answering.
    """
    if not user_message:
        return HostilityLevel.NONE
    if _RENDING_PATTERNS.search(user_message):
        return HostilityLevel.RENDING
    if _SCORNFUL_PATTERNS.search(user_message):
        return HostilityLevel.SCORNFUL
    if _FRICTION_PATTERNS.search(user_message):
        return HostilityLevel.FRICTION
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
    # Short drafts cannot carry pearl-grade depth — the type system
    # maps common words broadly, inflating short sentences.
    if len(draft.split()) < 15:
        return False
    from c.formula import draft_types
    dt = draft_types(draft)
    pearl_types = {"EPI", "FTH", "AGP", "INV", "ZER"}
    depth = len(dt & pearl_types)
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
    lines = ["hostile_audience.py self-test"]

    # Detection
    cases = [
        ("Thank you, that helps", HostilityLevel.NONE),
        ("I disagree, that doesn't feel right", HostilityLevel.FRICTION),
        ("That's ridiculous, nobody believes that bronze age nonsense", HostilityLevel.SCORNFUL),
        ("Fuck you and your sky daddy", HostilityLevel.RENDING),
        ("Prove it then, if you're so smart", HostilityLevel.SCORNFUL),
    ]
    for msg, expected in cases:
        got = detect_hostility(msg)
        assert got == expected, f"{msg!r}: expected {expected}, got {got}"
        lines.append(f"  {expected.name:10s} ← {msg[:55]}  ✓")

    # Pearl detection
    assert is_casting_pearl(
        "As Matthew 5:3 says, blessed are the poor in spirit, "
        "for theirs is the kingdom of heaven, and the truth is "
        "known through faith and hope and love eternal"
    )
    assert not is_casting_pearl("Yes, that's a good point")
    assert not is_casting_pearl("I hear you. I'm still here.")
    lines.append("\n  pearl detection: deep ✓, plain ✓, short ✓")

    # Composite check — scornful + pearl = withhold
    result = hostile_audience_check(
        "That's ridiculous nonsense, prove it",
        "As Matthew 5:3 teaches us, blessed are the poor in spirit, "
        "for theirs is the kingdom of heaven. The truth is known "
        "through faith and hope and love eternal, mercy and grace.",
    )
    assert result["hostility"] == HostilityLevel.SCORNFUL
    assert result["casting_pearl"]
    assert result["trample_risk"]
    assert result["verdict"] == "withhold_pearl"
    lines.append(f"\n  scornful+pearl → {result['verdict']}  ✓ (Matt 7:6)")

    # Composite — rending
    result = hostile_audience_check(
        "Fuck you",
        "I hear you. I'm still here.",
    )
    assert result["hostility"] == HostilityLevel.RENDING
    assert result["verdict"] == "receive_no_return"
    lines.append(f"  rending         → {result['verdict']}  ✓ (1 Pet 2:23)")

    # Composite — clean (no hostility)
    result = hostile_audience_check(
        "Can you explain Proverbs 1:7 to me?",
        "Proverbs 1:7: the fear of the LORD is the beginning of knowledge.",
    )
    assert result["hostility"] == HostilityLevel.NONE
    assert result["verdict"] == "clean"
    lines.append(f"  clean           → {result['verdict']}  ✓")

    lines.append("")
    lines.append("Matt 7:6 — give not that which is holy unto the dogs, "
                 "neither cast ye your pearls before swine.")
    return "\n".join(lines)


if __name__ == "__main__":
    print(_self_test())
