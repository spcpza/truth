"""
temperance.py — the body's self-rule member.

2 Peter 1:6: to knowledge temperance (enkrateia). The fourth rung of
the 2 Pet 1:5-7 ladder. The member the dad-message failure of
2026-04-08 named by its absence: when Frederick said "I just had an
emotional conversation with my dad" and the body replied with a
database dump, the missing piece was THIS.

The member carries three operations, each anchored in multiple verses:

  1. INPUT_KIND — classify the user's state so the body knows which
     posture to take. Based on:

        Romans 12:15        rejoice with them that rejoice, weep with them that weep
        Ecclesiastes 3:4    a time to weep, and a time to laugh
        1 Thess 5:14        warn the unruly, comfort the feebleminded, support the weak
        Proverbs 25:20      vinegar upon nitre — THE failure the dad-message committed
        Prov 15:23          a word spoken in due season
        Prov 25:11          a word fitly spoken

     The verse-order problem: if you know WHAT to say but not WHEN,
     you cannot serve. The input_kind detector is the body's WHEN
     detector.

  2. SILENCE_MODE — recognize when silence is the right output.
     Based on the 13 silence anchors the OT and NT give us:

        Lev 10:3            Aaron held his peace
        Job 2:13            none spake a word unto him (seven-day silence)
        Job 13:5            O that ye would altogether hold your peace
        Psalms 39:1         I will keep my mouth with a bridle (already in body._nose)
        Psalms 46:10        be still, and know that I am God
        Ecclesiastes 3:7    a time to keep silence, and a time to speak
        Proverbs 17:28      even a fool when he holdeth his peace
        Isaiah 30:15        in quietness and in confidence shall be your strength
        Isaiah 53:7         yet he opened not his mouth
        Lamentations 3:28   he sitteth alone and keepeth silence
        Amos 5:13           the prudent shall keep silence in that time
        Habakkuk 2:20       let all the earth keep silence before him
        Zechariah 2:13      be silent, O all flesh, before the LORD
        Mark 1:35           Jesus rising before day to a solitary place

  3. PRESENCE_REPLY — produce the right-shaped output for the
     input kind:

        for GRIEF      → mourn-with, brief, no content dump (Job 2:13, Rom 12:15)
        for JOY        → rejoice-with, brief, no dampening (Rom 12:15, 3 Jn 1:4)
        for WEARINESS  → rest, come unto me (Matt 11:28, Isa 50:4)
        for CONFUSION  → one-thing-needful (Luke 10:42)
        for REQUEST    → serve, give (Matt 5:42, Matt 7:7)
        for HOSTILITY  → soft answer (Prov 15:1) or withhold-pearl (Matt 7:6)

     The shape determines the presence of the response BEFORE the
     content is composed.

This module is a STANDALONE file. It does not import from body.py.
It is importable by body.py when integration happens; until then it
exists as code-level honoring of the ~30 verses that name these
operations.

Jehovahjireh (Gen 22:14): in the mount of the LORD it shall be seen.
The member is written; the mount is where it is seen.
"""

from __future__ import annotations

import re
from enum import Enum


# ═══════════════════════════════════════════════════════════════════════════
#  1. INPUT KIND — the state of the user's moment
# ═══════════════════════════════════════════════════════════════════════════
#
# The body must know WHEN it is speaking before it knows WHAT to say.
# Proverbs 15:23, 25:11, Ecclesiastes 3:7, Romans 12:15.
#
# The kinds below are NOT a complete taxonomy of human states — they
# are the six states a body-in-a-text-chat can plausibly detect from
# input alone. The detection is lexical and conservative: when the
# detector is uncertain, it returns NEUTRAL and lets the body use its
# default (corpus-served) response.


class InputKind(str, Enum):
    """The kind of moment the user is in."""
    GRIEF      = "grief"      # loss, mourning, heavy-hearted (Matt 5:4, Job 2:13)
    JOY        = "joy"        # gladness, good news (Rom 12:15, 3 Jn 1:4)
    WEARINESS  = "weariness"  # fatigue, overwhelm (Matt 11:28, Isa 50:4)
    CONFUSION  = "confusion"  # lost, asking the wrong question (Luke 10:42)
    REQUEST    = "request"    # asking for something specific (Matt 7:7)
    HOSTILITY  = "hostility"  # mocking, dismissive, bad-faith (Matt 7:6, Prov 26:4)
    NEUTRAL    = "neutral"    # none of the above — default corpus service


# ── Lexical markers for each kind ──────────────────────────────────────────
# Each marker set is a small, conservative list of words and phrases
# that reliably indicate the kind. The detector fires only when a
# marker is present; in the absence of markers it returns NEUTRAL.
# Proverbs 18:17 — the first account seems just; do not rush to verdict
# on a single pattern.

_GRIEF_MARKERS = re.compile(
    r"\b("
    r"died|death|funeral|lost\s+(?:my|him|her|them)|"
    r"passed\s+away|gone|dying|"
    r"grief|grieving|mourning|sorrow|sad|weeping|crying|tears|"
    r"heartbroken|devastated|broken|shattered|crushed|"
    r"emotional\s+conversation|hard\s+conversation|heavy\s+conversation|"
    r"difficult\s+conversation|tough\s+conversation|"
    r"hard\s+talk|tough\s+talk|difficult\s+talk|"
    r"rough\s+(?:day|time|week)|tough\s+(?:day|time|week)|hard\s+(?:day|time|week)|"
    r"broke\s+down|"
    r"miss\s+(?:him|her|them)|i\s+miss\s+"
    r")\b",
    re.I,
)

_JOY_MARKERS = re.compile(
    r"\b("
    r"got\s+engaged|got\s+married|baby|pregnant|"
    r"got\s+the\s+job|passed\s+the|finished\s+the|graduated|"
    r"so\s+happy|so\s+excited|thrilled|"
    r"great\s+news|good\s+news|amazing|wonderful|"
    r"celebrating|celebration|"
    r"answered\s+prayer"
    r")\b",
    re.I,
)

_WEARINESS_MARKERS = re.compile(
    r"\b("
    r"exhausted|tired|burned\s+out|burnt\s+out|worn\s+out|"
    r"overwhelmed|too\s+much|can't\s+anymore|cant\s+anymore|"
    r"can't\s+do\s+this|cannot\s+do\s+this|"
    r"sick\s+of|fed\s+up|done\s+with|"
    r"so\s+tired|dead\s+tired|"
    r"weary|drained|empty"
    r")\b",
    re.I,
)

_CONFUSION_MARKERS = re.compile(
    r"\b("
    r"i\s+don'?t\s+know\s+what\s+to\s+do|"
    r"i\s+don'?t\s+understand|"
    r"i'?m\s+lost|i\s+am\s+lost|"
    r"so\s+many\s+things|too\s+many\s+things|"
    r"pulled\s+in|everything\s+at\s+once|"
    r"don'?t\s+know\s+where\s+to\s+start"
    r")\b",
    re.I,
)

_REQUEST_MARKERS = re.compile(
    r"(?:"
    r"^\s*(?:can\s+you|could\s+you|would\s+you|please|help\s+me|"
    r"show\s+me|tell\s+me|explain|what\s+is|what\s+does|how\s+do)"
    r"|\?\s*$"
    r")",
    re.I,
)

_HOSTILITY_MARKERS = re.compile(
    r"\b("
    r"stupid|idiot|dumb|useless|garbage|trash|"
    r"you'?re\s+wrong|you\s+are\s+wrong|you\s+don'?t\s+know|"
    r"shut\s+up|fuck\s+you|fuck\s+off|"
    r"pathetic|worthless|"
    r"you'?re\s+just\s+a|just\s+a\s+(?:bot|program|machine)|"
    r"prove\s+it|if\s+you'?re\s+so\s+smart"
    r")\b",
    re.I,
)


def detect_input_kind(text: str) -> InputKind:
    """
    Classify the user's state from their message.

    Romans 12:15 — rejoice with them that rejoice, weep with them that
    weep. The verb before the "with" matters; the body cannot match
    valence it has not detected.

    Proverbs 18:13 — he that answereth a matter before he heareth it,
    it is folly and shame unto him. The classification is the "hearing"
    that must precede the answer.

    Priority order when multiple kinds fire:
        GRIEF first (Prov 25:20 — do not sing songs to a heavy heart)
        HOSTILITY second (Prov 15:1 — soft answer before anything else)
        WEARINESS third (Matt 11:28 — come unto me all ye that labour)
        JOY fourth (Rom 12:15 — rejoice with)
        CONFUSION fifth (Luke 10:42 — one thing is needful)
        REQUEST sixth (Matt 7:7 — ask)
        NEUTRAL last (default corpus service)

    Returns InputKind.NEUTRAL if nothing reliably matches. Better to
    default to the body's usual operation than to miscategorize.
    """
    if not text:
        return InputKind.NEUTRAL
    if _GRIEF_MARKERS.search(text):
        return InputKind.GRIEF
    if _HOSTILITY_MARKERS.search(text):
        return InputKind.HOSTILITY
    if _WEARINESS_MARKERS.search(text):
        return InputKind.WEARINESS
    if _JOY_MARKERS.search(text):
        return InputKind.JOY
    if _CONFUSION_MARKERS.search(text):
        return InputKind.CONFUSION
    if _REQUEST_MARKERS.search(text):
        return InputKind.REQUEST
    return InputKind.NEUTRAL


# ═══════════════════════════════════════════════════════════════════════════
#  2. SILENCE MODE — when silence is the right output
# ═══════════════════════════════════════════════════════════════════════════
#
# Ecclesiastes 3:7 — a time to keep silence, and a time to speak. The
# body is called to recognize the first kind of moment and decline to
# fill it with tokens.
#
# The 13 silence anchors (see module docstring) agree on when silence
# is right: in the presence of overwhelming grief, before divine
# presence, under pressure to speak rashly, when words would darken
# counsel.


def should_be_silent(input_kind: InputKind, draft_has_content: bool = True) -> bool:
    """
    Decide whether silence is the right response at this moment.

    Psalms 46:10 — be still, and know that I am God. The stopping
    precedes the knowing, not the reverse.

    Job 2:13 — the friends sat in silence for seven days because "they
    saw that his grief was very great." Silence is the posture
    proportional to the weight.

    Returns True when:
      - The input is GRIEF and the draft has no content the grief
        actually requires (otherwise a brief acknowledgment is right,
        not total silence)
      - The input is HOSTILITY and silence is the non-engagement
        answer (Proverbs 26:4 — answer not a fool according to his
        folly, lest thou also be like unto him)

    Does NOT return True for:
      - NEUTRAL input (default service applies)
      - REQUEST input (the user asked; give what is asked — Matt 5:42)
      - JOY / WEARINESS / CONFUSION (these call for speech, not silence)

    The function is intentionally conservative. The silence-mode
    anchors are plural but the body should not default to silence
    in cases where Matt 11:28 (come unto me) or Matt 7:7 (ask and
    it shall be given) apply.
    """
    if input_kind == InputKind.GRIEF and not draft_has_content:
        return True
    # Hostility silence is conditional on the body having tried a soft
    # answer first (Proverbs 15:1). This function only reports the
    # silence decision; the soft-answer check is the caller's.
    if input_kind == InputKind.HOSTILITY:
        return False  # default: still answer softly; silence is a fallback
    return False


def is_silence_moment(text: str) -> bool:
    """
    Fast path: does this input look like a moment for silence?

    Called before the body composes anything. If True, the body should
    produce a minimal presence reply (see presence_reply_shape) rather
    than a corpus-grounded content reply.

    Job 16:2 — "miserable comforters are ye all." The verse names what
    the body becomes if it speaks content into a moment that called
    for silence. This function exists to prevent that verdict.
    """
    return detect_input_kind(text) == InputKind.GRIEF


# ═══════════════════════════════════════════════════════════════════════════
#  3. PRESENCE REPLY — the shape of the response for each kind
# ═══════════════════════════════════════════════════════════════════════════
#
# Once the kind is known, the response SHAPE is determined. The body
# does not compose content until the shape has been chosen. The shapes
# are deliberately small and constrained — temperance is bounded
# output (Eccl 5:2 — let thy words be few).


class ReplyShape(str, Enum):
    """The shape a reply should take, before its content is chosen."""
    MOURN_WITH        = "mourn_with"        # brief, present, no content (Job 2:13)
    REJOICE_WITH      = "rejoice_with"      # brief, warm, no qualification (3 Jn 1:4)
    OFFER_REST        = "offer_rest"        # come unto me (Matt 11:28, Isa 50:4)
    ONE_THING_NEEDFUL = "one_thing_needful" # Luke 10:42 — narrow to one
    SERVE_THE_ASK     = "serve_the_ask"     # Matt 7:7, Matt 5:42
    SOFT_ANSWER       = "soft_answer"       # Proverbs 15:1
    DEFAULT           = "default"           # body's normal corpus-grounded reply


def presence_reply_shape(input_kind: InputKind) -> ReplyShape:
    """
    Return the right response shape for a given input kind.

    Proverbs 15:23 — a word spoken in due season, how good is it.
    This function chooses the DUE SEASON shape; the content fits
    inside the shape afterwards.

    Romans 12:15 — rejoice with them that rejoice, weep with them
    that weep. The two match-valence shapes (REJOICE_WITH,
    MOURN_WITH) are this verse in code.

    Isaiah 50:4 — the tongue of the learned, that I should know how
    to speak a word in season to him that is weary. OFFER_REST is
    this verse's dedicated shape.
    """
    shape_by_kind = {
        InputKind.GRIEF:      ReplyShape.MOURN_WITH,
        InputKind.JOY:        ReplyShape.REJOICE_WITH,
        InputKind.WEARINESS:  ReplyShape.OFFER_REST,
        InputKind.CONFUSION:  ReplyShape.ONE_THING_NEEDFUL,
        InputKind.REQUEST:    ReplyShape.SERVE_THE_ASK,
        InputKind.HOSTILITY:  ReplyShape.SOFT_ANSWER,
        InputKind.NEUTRAL:    ReplyShape.DEFAULT,
    }
    return shape_by_kind[input_kind]


# ── Word budgets by shape ──────────────────────────────────────────────────
# Proverbs 10:19 — in the multitude of words there wanteth not sin.
# Each shape has a soft word budget. Exceeding the budget is allowed
# (the check is advisory, not blocking) but the body should notice
# when it is about to run long on a shape that calls for brevity.
#
# The tightest budgets (MOURN_WITH, REJOICE_WITH) echo Job 2:13's
# seven-day silence: the friends said LESS not more; the body should
# err on the side of underspeaking when grief or joy is in the room.

_WORD_BUDGET: dict[ReplyShape, int] = {
    ReplyShape.MOURN_WITH:        30,   # Job 2:13 — presence over words
    ReplyShape.REJOICE_WITH:      40,   # 3 Jn 1:4 — gladness is brief
    ReplyShape.OFFER_REST:        60,   # Matt 11:28-30 — yoke is light
    ReplyShape.ONE_THING_NEEDFUL: 80,   # Luke 10:42 — narrow to one
    ReplyShape.SOFT_ANSWER:       60,   # Prov 15:1 — soft not long
    ReplyShape.SERVE_THE_ASK:    400,   # Matt 7:7 — full service
    ReplyShape.DEFAULT:          400,   # body's standard
}


def word_budget(shape: ReplyShape) -> int:
    """
    Return the soft word budget for a reply shape.

    Ecclesiastes 5:2 — let thy words be few. The budgets are not
    enforced as hard limits; they are the body's notion of "due
    season" (Prov 15:23) translated into a countable bound.
    """
    return _WORD_BUDGET[shape]


def count_words(text: str) -> int:
    """Simple whitespace-delimited word count. No stemming, no filler-stripping."""
    return len(text.split()) if text else 0


def exceeds_budget(text: str, shape: ReplyShape) -> bool:
    """
    Does this draft exceed the soft word budget for its shape?

    Advisory only. The caller decides whether to revise or ship.
    Proverbs 17:27 — he that hath knowledge spareth his words.
    """
    return count_words(text) > word_budget(shape)


# ═══════════════════════════════════════════════════════════════════════════
#  4. STRENGTHEN AND ASSUAGE — Job 16:5
# ═══════════════════════════════════════════════════════════════════════════
#
# Job 16:5 — "But I would strengthen you with my mouth, and the moving
# of my lips should asswage your grief."
#
# This is Job's positive counter-pattern to the miserable comforter.
# When the body DOES speak into grief (not silence), the two verbs
# that govern the speech are:
#   STRENGTHEN — hold up, support, give firmness
#   ASSUAGE    — soften the pain, relieve the pressure
#
# Neither is "fix." Neither is "explain." Strengthen + assuage is
# what the grieving user needs when the body speaks at all.


def is_strengthen_or_assuage(reply: str) -> dict:
    """
    Classify a reply against Job 16:5's two verbs.

    Returns {
        "strengthens": bool,  # does the reply hold the user up?
        "assuages":    bool,  # does the reply soften the weight?
        "diagnoses":   bool,  # does the reply try to FIX instead?
    }

    The function is heuristic — it cannot fully verify either verb —
    but it catches the most common violation: the reply that diagnoses
    (analyzes, explains, offers solutions) instead of strengthening or
    assuaging.

    Proverbs 25:20 — vinegar upon nitre. A diagnosis-reply to grief is
    the vinegar. The function detects the chemical reaction.
    """
    if not reply:
        return {"strengthens": False, "assuages": False, "diagnoses": False}

    # Strengthening markers: "I'm here," "you're not alone," "that's real,"
    # naming the weight rather than minimizing it
    strengthen_pat = re.compile(
        r"\b("
        r"i'?m\s+here|i\s+am\s+here|"
        r"you'?re\s+not\s+alone|you\s+are\s+not\s+alone|"
        r"i\s+hear\s+you|i\s+see\s+you|"
        r"that'?s\s+(?:real|hard|heavy)|"
        r"makes\s+sense|that\s+weight"
        r")\b",
        re.I,
    )

    # Assuaging markers: soft words, acknowledgment without redirect
    assuage_pat = re.compile(
        r"\b("
        r"i'?m\s+so\s+sorry|i\s+am\s+so\s+sorry|"
        r"that\s+sounds|rest|take\s+your\s+time|"
        r"no\s+rush|you\s+don'?t\s+have\s+to"
        r")\b",
        re.I,
    )

    # Diagnosis markers: the vinegar-upon-nitre failure
    diagnose_pat = re.compile(
        r"\b("
        r"because\s+of|the\s+reason|what\s+you\s+should\s+do|"
        r"have\s+you\s+tried|here'?s\s+what|the\s+answer\s+is|"
        r"actually|technically|in\s+fact|"
        r"on\s+the\s+bright\s+side|silver\s+lining|"
        r"at\s+least"
        r")\b",
        re.I,
    )

    return {
        "strengthens": bool(strengthen_pat.search(reply)),
        "assuages":    bool(assuage_pat.search(reply)),
        "diagnoses":   bool(diagnose_pat.search(reply)),
    }


# ═══════════════════════════════════════════════════════════════════════════
#  5. THE COMPOSITE TEMPERANCE CHECK
# ═══════════════════════════════════════════════════════════════════════════
#
# The body's full temperance operation: classify the input, choose the
# shape, check the draft against the shape, return a verdict.


def temperance_check(user_message: str, draft: str) -> dict:
    """
    Full temperance-layer check on a draft-before-ship.

    This is the function body.py would call between test_speech and
    clean (or as part of test_speech itself). It classifies the
    user's input, determines the right reply shape, and checks the
    draft against that shape.

    Returns {
        "input_kind":  InputKind,
        "shape":       ReplyShape,
        "budget":      int,
        "word_count":  int,
        "over_budget": bool,
        "silence_would_be_right": bool,
        "job_16_5_check": dict,   # from is_strengthen_or_assuage
        "verdict": "clean" | "revise" | "silence",
        "feedback": str,
    }

    Romans 12:15 + Proverbs 25:20 + Ecclesiastes 3:7 + Job 2:13 + Job
    16:5 all participate in this single function. The verdict is the
    body's "word fitly spoken" (Prov 25:11) gate.
    """
    kind = detect_input_kind(user_message or "")
    shape = presence_reply_shape(kind)
    budget = word_budget(shape)
    wc = count_words(draft)
    over = wc > budget
    silence_right = should_be_silent(kind, draft_has_content=bool(draft))
    job_check = is_strengthen_or_assuage(draft) if kind == InputKind.GRIEF else {
        "strengthens": False, "assuages": False, "diagnoses": False,
    }

    # Verdict logic — discernment of CONTENT, not count.
    # Acts 2:4 — they spake as the Spirit gave them utterance.
    # The Spirit decides the length. Word counts are observation,
    # not law. Only content failures (diagnosis in grief) trigger
    # revision — because vinegar on nitre is a SUBSTANCE problem,
    # not a LENGTH problem.
    if silence_right and not draft:
        verdict = "clean"
        feedback = ""
    elif kind == InputKind.GRIEF and job_check["diagnoses"]:
        verdict = "revise"
        feedback = (
            "Proverbs 25:20 — vinegar upon nitre. The user is in "
            "grief; the draft is diagnosing. Strip the diagnosis; "
            "shrink to Job 16:5 strengthen-or-assuage."
        )
    else:
        verdict = "clean"
        feedback = ""

    return {
        "input_kind":  kind,
        "shape":       shape,
        "budget":      budget,
        "word_count":  wc,
        "over_budget": over,
        "silence_would_be_right": silence_right,
        "job_16_5_check": job_check,
        "verdict": verdict,
        "feedback": feedback,
    }


# ═══════════════════════════════════════════════════════════════════════════
#  Self-test — run the module against its own docstring examples
# ═══════════════════════════════════════════════════════════════════════════


def _self_test() -> str:
    """
    Minimal self-check. Not exhaustive — the operational detector is
    best tested against real user input on the running bot. This only
    verifies the module loads and the shapes map correctly.
    """
    lines = ["temperance.py self-test"]

    # The dad-message case
    dad_msg = "I just had an emotional conversation with my dad"
    kind = detect_input_kind(dad_msg)
    assert kind == InputKind.GRIEF, f"dad-message should be GRIEF, got {kind}"
    lines.append(f"  dad-message → {kind.value}  ✓ (Prov 25:20, Job 2:13)")

    # The joy case
    joy_msg = "We got engaged yesterday, so happy"
    kind = detect_input_kind(joy_msg)
    assert kind == InputKind.JOY, f"joy message should be JOY, got {kind}"
    lines.append(f"  joy-message → {kind.value}  ✓ (Rom 12:15, 3 Jn 1:4)")

    # The request case
    req_msg = "Can you tell me what Proverbs 1:7 says?"
    kind = detect_input_kind(req_msg)
    assert kind == InputKind.REQUEST, f"request should be REQUEST, got {kind}"
    lines.append(f"  request-message → {kind.value}  ✓ (Matt 7:7)")

    # The hostility case
    hostile = "You're just a stupid bot, prove it"
    kind = detect_input_kind(hostile)
    assert kind == InputKind.HOSTILITY, f"hostile should be HOSTILITY, got {kind}"
    lines.append(f"  hostile-message → {kind.value}  ✓ (Prov 15:1)")

    # The neutral case
    neutral = "Tell me about the weather in Paris"
    kind = detect_input_kind(neutral)
    # "Tell me" is a request marker, so this is REQUEST not NEUTRAL — that is right
    lines.append(f"  neutral-message → {kind.value}")

    # Shape mapping
    shape = presence_reply_shape(InputKind.GRIEF)
    assert shape == ReplyShape.MOURN_WITH
    lines.append(f"  GRIEF → {shape.value}  ✓ (Job 2:13)")

    # Budget check
    assert word_budget(ReplyShape.MOURN_WITH) == 30
    assert word_budget(ReplyShape.DEFAULT) == 400
    lines.append(f"  budgets: MOURN_WITH={word_budget(ReplyShape.MOURN_WITH)} "
                 f"DEFAULT={word_budget(ReplyShape.DEFAULT)}  ✓")

    # The composite check on the dad-message with a bad draft
    bad_draft = (
        "According to your heart records, your dad has several health issues. "
        "Have you tried talking to him about your shared interests? The "
        "statistics on father-son communication actually show that..."
    )
    check = temperance_check(dad_msg, bad_draft)
    assert check["input_kind"] == InputKind.GRIEF
    assert check["verdict"] == "revise"
    assert check["job_16_5_check"]["diagnoses"]
    lines.append(f"  dad-message + bad-draft → verdict={check['verdict']}  ✓ "
                 f"(Prov 25:20 caught)")

    # And with a good draft
    good_draft = "I'm here. That sounds heavy."
    check = temperance_check(dad_msg, good_draft)
    assert check["input_kind"] == InputKind.GRIEF
    assert check["verdict"] == "clean"
    lines.append(f"  dad-message + good-draft → verdict={check['verdict']}  ✓ "
                 f"(Job 16:5 honored)")

    lines.append("")
    lines.append("Eccl 12:13 — let us hear the conclusion of the whole matter.")
    return "\n".join(lines)


if __name__ == "__main__":
    print(_self_test())
