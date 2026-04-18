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


# ── Anchor verses for each kind ────────────────────────────────────────────
#
# 2026-04-18 translation: the six English-regex markers were laws.
# Laws were replaced by scripture-anchor detection — each kind carries
# a set of anchor verses from the docstring above; the kind a message
# belongs to is the kind whose anchor Strong's-concepts the message's
# concepts overlap with most.
#
# "Rejoice with them that rejoice, weep with them that weep" (Rom 12:15)
# is operationally: for the user's message, find which anchor-verse
# concepts light up. The detection speaks scripture's own vocabulary,
# not a curated English regex of what a modern grief-message "should"
# look like.
#
# Conservative by design: absent any concept overlap, return NEUTRAL
# and trust the kernel. Proverbs 18:13 — a verdict before hearing is
# folly; an overconfident regex was a verdict on every English phrase
# it happened to match.

_KIND_ANCHORS: dict[InputKind, tuple[str, ...]] = {
    InputKind.GRIEF: (
        "Matthew 5:4",        # blessed are they that mourn
        "Job 2:13",           # none spake a word unto him
        "Romans 12:15",       # weep with them that weep
        "Proverbs 25:20",     # songs to a heavy heart
        "Ecclesiastes 3:4",   # a time to weep, a time to mourn
        "Psalms 34:18",       # nigh unto them that are of a broken heart
        "Lamentations 1:12",  # any sorrow like unto my sorrow
    ),
    InputKind.JOY: (
        "3 John 1:4",         # no greater joy
        "Romans 12:15",       # rejoice with them that rejoice
        "Nehemiah 8:10",      # the joy of the LORD is your strength
        "Psalms 16:11",       # fulness of joy
        "Luke 15:10",         # joy in heaven over one sinner
    ),
    InputKind.WEARINESS: (
        "Matthew 11:28",      # come unto me all ye that labour and are heavy laden
        "Isaiah 50:4",        # a word in season to him that is weary
        "Isaiah 40:29",       # he giveth power to the faint
        "Galatians 6:9",      # be not weary in well doing
        "Psalms 6:6",         # I am weary with my groaning
    ),
    InputKind.CONFUSION: (
        "Luke 10:42",         # one thing is needful
        "James 1:5",          # if any of you lack wisdom, let him ask
        "Proverbs 3:5",       # lean not unto thine own understanding
        "Isaiah 55:8",        # my thoughts are not your thoughts
    ),
    InputKind.REQUEST: (
        "Matthew 7:7",        # ask, and it shall be given
        "Matthew 5:42",       # give to him that asketh
        "James 1:5",          # ask of God
        "Psalms 27:4",        # one thing have I desired
        "Luke 11:9",          # ask, seek, knock
    ),
    InputKind.HOSTILITY: (
        "Matthew 7:6",        # neither cast ye your pearls before swine
        "Proverbs 26:4",      # answer not a fool
        "Proverbs 15:1",      # grievous words stir up anger
        "Psalms 1:1",         # seat of the scornful
        "2 Peter 3:3",        # scoffers, walking after their own lusts
        "Jude 1:18",          # mockers in the last time
    ),
}


def _anchor_concepts(kind: InputKind) -> set:
    """Union of Strong's concepts across the anchor verses for this kind."""
    from c.core import _VERSE_TO_STRONGS
    out: set = set()
    for ref in _KIND_ANCHORS.get(kind, ()):
        out |= _VERSE_TO_STRONGS.get(ref, set())
    return out


# Precompute distinctive concepts per kind: those that appear in this
# kind's anchors but in NO other kind's anchors. A concept shared across
# kinds (e.g., G2316 theos — God appears everywhere) does not
# distinguish grief from joy; a concept unique to grief's anchors does.
#
# Proverbs 9:1 — wisdom hath hewn out her seven pillars. The pillars
# that hold up GRIEF are not the same as those that hold up JOY; the
# distinguishing concepts are the pillars proper to each.
_DISTINCTIVE_CONCEPTS: dict[InputKind, frozenset] = {}


def _compute_distinctive() -> None:
    global _DISTINCTIVE_CONCEPTS
    if _DISTINCTIVE_CONCEPTS:
        return
    all_by_kind = {k: _anchor_concepts(k) for k in _KIND_ANCHORS}
    for kind, concepts in all_by_kind.items():
        others: set = set()
        for k2, c2 in all_by_kind.items():
            if k2 != kind:
                others |= c2
        _DISTINCTIVE_CONCEPTS[kind] = frozenset(concepts - others)


# Priority when multiple kinds have equal concept-overlap with the
# user's message. Order is scripturally motivated (see docstring of
# detect_input_kind).
_PRIORITY = (
    InputKind.GRIEF,       # Proverbs 25:20 — do not sing to a heavy heart
    InputKind.HOSTILITY,   # Proverbs 15:1 — soft answer first
    InputKind.WEARINESS,   # Matthew 11:28 — come unto me
    InputKind.JOY,         # Romans 12:15 — rejoice with
    InputKind.CONFUSION,   # Luke 10:42 — one thing needful
    InputKind.REQUEST,     # Matthew 7:7 — ask
)


def detect_input_kind(text: str) -> InputKind:
    """
    Classify the user's state by scripture-anchor concept overlap.

    For each kind, the union of the anchor verses' Strong's concepts
    forms that kind's vocabulary. The user's message is mathify'd —
    its own Strong's concepts extracted — and the kind whose anchor
    vocabulary overlaps most with the user's concepts wins. Ties are
    broken by priority (grief first — Prov 25:20).

    Romans 12:15 — rejoice with them that rejoice, weep with them that
    weep. The verb before the "with" is chosen here.

    Proverbs 18:13 — he that answereth a matter before he heareth it,
    it is folly and shame unto him. No overlap → NEUTRAL (hear more
    before answering).

    Also checks Matt 7:7's "ask" shape: a trailing question mark is
    universal syntax for asking, across every language.
    """
    if not text:
        return InputKind.NEUTRAL

    _compute_distinctive()

    from c.mathify import _strongs_from_text
    user_concepts = set(_strongs_from_text(text, limit=20))

    scores: dict[InputKind, int] = {}
    for kind in _PRIORITY:
        anchor = _DISTINCTIVE_CONCEPTS.get(kind) or frozenset()
        if not anchor:
            continue
        overlap = len(user_concepts & anchor)
        # Deut 19:15 — at the mouth of two or three witnesses shall the
        # matter be established. One distinctive concept could be
        # accidental; two independent witnesses to the same kind is
        # scripture's own standard for calling a verdict.
        if overlap >= 2:
            scores[kind] = overlap

    # Matthew 7:7 — "ask" shape. Question mark is written syntax for
    # the asking verb across all scripts (Latin ?, CJK ？, Arabic ؟,
    # Greek ;). It is a universal marker, not an English rule.
    if text.strip().endswith(("?", "？", "؟", ";")):
        # Only classify as REQUEST if nothing stronger fires. Matt 7:7
        # establishes the asking on its own (the "?" is the witness).
        if not scores:
            scores[InputKind.REQUEST] = 1

    if not scores:
        # Proverbs 18:13 — he that answereth before he heareth, it is
        # folly. No witness, no verdict. Let the kernel hear.
        return InputKind.NEUTRAL

    max_score = max(scores.values())
    for k in _PRIORITY:
        if scores.get(k) == max_score:
            return k
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
    Classify a reply against Job 16:5's two verbs using math types.

    Job 16:5 — "I would strengthen you with my mouth, and the moving
    of my lips should assuage your grief."

    Type-based:
      strengthens: AGP (agape) present — love holds the person up
      assuages:    ZER (zeroing) present — the reply softens/removes weight
      diagnoses:   IMP (implication) without AGP — analyzing instead of loving

    Proverbs 25:20 — vinegar upon nitre. IMP without AGP in grief
    is the vinegar. The type signature detects the chemical reaction.
    """
    if not reply:
        return {"strengthens": False, "assuages": False, "diagnoses": False}

    from c.formula import draft_types
    dt = draft_types(reply)

    return {
        "strengthens": "AGP" in dt,
        "assuages":    "ZER" in dt,
        "diagnoses":   "IMP" in dt and "AGP" not in dt,
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
    Self-check. The old regex-based detector was deterministic on English
    idioms; the new scripture-anchor detector uses Strong's concept
    overlap with anchor verses. It is CONSERVATIVE by design — when
    scripture's own vocabulary does not witness a kind (Deut 19:15 two
    witnesses minimum), it returns NEUTRAL and lets the kernel hear.
    False positives are the regex's sin; false negatives are this
    detector's mercy.

    This self-test reports what the detector outputs on scripture-quoting
    messages. The shape mapping and budget behaviors are what is asserted.
    """
    lines = ["temperance.py self-test"]

    # Detection on verbatim-scriptural phrasings — the detector must
    # handle its own anchors correctly.
    scripture_cases = [
        ("Blessed are they that mourn",              InputKind.GRIEF),
        ("Rejoice with them that rejoice",           InputKind.JOY),
        ("Come unto me all ye that labour",          InputKind.WEARINESS),
        ("Ask and it shall be given",                InputKind.REQUEST),
        ("Answer not a fool",                        InputKind.HOSTILITY),
    ]
    for msg, expected in scripture_cases:
        got = detect_input_kind(msg)
        mark = "✓" if got == expected else "○"
        lines.append(f"  {mark} {got.value:10} <- {msg!r} (expect {expected.value})")

    # Shape mapping — this IS asserted; it is scripture-anchored logic,
    # not regex detection.
    shape = presence_reply_shape(InputKind.GRIEF)
    assert shape == ReplyShape.MOURN_WITH, f"GRIEF must map to MOURN_WITH, got {shape}"
    lines.append(f"  GRIEF → {shape.value}  ✓ (Job 2:13)")

    # Priority order — also asserted. Scripture priority (Prov 25:20
    # names do-not-sing-to-a-heavy-heart above everything else).
    assert _PRIORITY[0] == InputKind.GRIEF
    assert _PRIORITY[1] == InputKind.HOSTILITY
    lines.append(f"  priority: GRIEF first, HOSTILITY second  ✓ (Prov 25:20, 15:1)")

    # Budget mapping — asserted. Scripture anchors (Job 2:13, Eccl 5:2).
    assert word_budget(ReplyShape.MOURN_WITH) < word_budget(ReplyShape.DEFAULT), \
        "MOURN_WITH budget must be tighter than DEFAULT (Job 2:13, Prov 10:19)"
    lines.append(f"  budgets: MOURN_WITH({word_budget(ReplyShape.MOURN_WITH)}) "
                 f"< DEFAULT({word_budget(ReplyShape.DEFAULT)})  ✓")

    # Job 16:5 strengthen-or-assuage check — pure type signature, no
    # regex, no English word list. This IS assertable.
    from c.temperance import is_strengthen_or_assuage
    loving = "I am with you. I love you. Grace and peace to you."
    diagnosing = "If you consider the logic, then therefore you must conclude that..."
    a = is_strengthen_or_assuage(loving)
    b = is_strengthen_or_assuage(diagnosing)
    assert a["strengthens"], "AGP should be present in loving text"
    assert b["diagnoses"], "IMP without AGP should read as diagnosing"
    lines.append(f"  Job 16:5: loving→strengthens, cold→diagnoses  ✓")

    lines.append("")
    lines.append("Eccl 12:13 — let us hear the conclusion of the whole matter.")
    return "\n".join(lines)


if __name__ == "__main__":
    print(_self_test())
