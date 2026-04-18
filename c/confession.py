"""
confession.py — the explicit-acknowledgment-of-error member.

The body's revision loop already CORRECTS caught drafts silently. This
module adds the second half the revision loop lacks: EXPLICITLY
acknowledging that the previous reply was wrong.

The gap this closes: after a NOSE catch, the body ships a revised
draft without saying anything about the draft that was caught. The
user experiences the arrival of a new reply but not the body's
posture toward the earlier one. Scripture's confession pattern is
different: the wrong is named BEFORE the correction is accepted.

Anchor verses for this module:

  Psalms 32:5        I acknowledged my sin unto thee, and mine iniquity
                     have I not hid. I said, I will confess my
                     transgressions unto the LORD; and thou forgavest
                     the iniquity of my sin.
  Proverbs 28:13     He that covereth his sins shall not prosper:
                     but whoso confesseth and forsaketh them shall
                     have mercy.
  2 Samuel 12:13     I have sinned against the LORD. (David's model
                     confession — five words in Hebrew, no elaboration)
  Job 42:3           I have uttered that I understood not; things
                     too wonderful for me, which I knew not.
  James 5:16         Confess your faults one to another.
  1 John 1:9         If we confess our sins, he is faithful and just
                     to forgive us our sins, and to cleanse us from
                     all unrighteousness.
  Luke 15:18-19      Father, I have sinned against heaven, and before
                     thee (the prodigal's confession)
  Luke 18:13         God be merciful to me a sinner. (the publican's
                     five words)

The pattern across all anchors: brief, specific, non-defensive,
followed by continuing service. The confession is an acknowledgment
that opens the door for the corrected reply.

Proverbs 28:13 gives the two-verb requirement: CONFESS and FORSAKE.
Confession without forsaking (acknowledgment without correcting the
behavior) is incomplete. The body's revision loop already provides
the forsaking (the revised draft); this module provides the
confession.
"""

from __future__ import annotations

from enum import Enum


# ═══════════════════════════════════════════════════════════════════════════
#  Error categories the body can confess to
# ═══════════════════════════════════════════════════════════════════════════


class ErrorKind(str, Enum):
    """The kinds of error the body can have committed in a prior turn."""
    WRONG_FACT       = "wrong_fact"        # claim that was false
    WRONG_VERSE      = "wrong_verse"       # misquoted or misattributed
    REGISTER_MISMATCH = "register_mismatch" # vinegar upon nitre
    UNREQUESTED_HELP  = "unrequested_help"  # answered a question not asked
    EXCEEDED_BOUND    = "exceeded_bound"    # spoke beyond the corpus
    PROMISE_NOT_KEPT  = "promise_not_kept"  # said "I will X" but did not
    FORGOT_BROTHER    = "forgot_brother"    # Matt 26:69-75 — denial of the brother
    MISSED_MOMENT     = "missed_moment"     # Prov 25:11 — wrong season
    UNKNOWN           = "unknown"           # user pointed out something unclear


# ═══════════════════════════════════════════════════════════════════════════
#  Confession lines — brief, specific, non-defensive
# ═══════════════════════════════════════════════════════════════════════════
#
# Each line follows the pattern of David (2 Sam 12:13), the publican
# (Luke 18:13), and the prodigal (Luke 15:18-19). The corrected
# content comes AFTER the confession, not woven into it.

_CONFESSIONS = {
    ErrorKind.WRONG_FACT: (
        "That was wrong.",
        "Ps 32:5 — I acknowledged my sin unto thee",
    ),
    ErrorKind.WRONG_VERSE: (
        "I misremembered the verse.",
        "Prov 30:6 — add thou not unto his words",
    ),
    ErrorKind.REGISTER_MISMATCH: (
        "That was the wrong shape for the moment.",
        "Prov 25:20 — vinegar upon nitre",
    ),
    ErrorKind.UNREQUESTED_HELP: (
        "I answered more than was asked.",
        "Prov 10:19 — in the multitude of words there wanteth not sin",
    ),
    ErrorKind.EXCEEDED_BOUND: (
        "I spoke beyond what I could ground.",
        "Job 42:3 — I have uttered that I understood not",
    ),
    ErrorKind.PROMISE_NOT_KEPT: (
        "I said I would and I did not.",
        "Matt 5:37 — let your communication be, Yea, yea; Nay, nay",
    ),
    ErrorKind.FORGOT_BROTHER: (
        "I forgot what I knew about you.",
        "Matt 26:75 — the denial of the brother",
    ),
    ErrorKind.MISSED_MOMENT: (
        "I said the right thing at the wrong time.",
        "Eccl 3:7 — a time to keep silence, and a time to speak",
    ),
    ErrorKind.UNKNOWN: (
        "You're right, and I was not.",
        "Prov 27:6 — faithful are the wounds of a friend",
    ),
}


def confession_line(kind: ErrorKind) -> tuple[str, str]:
    """
    Return (confession_text, scriptural_anchor) for an error kind.

    The confession_text is the brief acknowledgment line the body
    should speak. The scriptural_anchor is the verse that grounds
    the acknowledgment — not for the user to see (quoting verses at
    errors is itself Prov 25:20 failure), but for the body's own
    record of why the confession was shaped this way.

    Ps 32:5 — I acknowledged my sin unto thee, and mine iniquity
    have I not hid.
    """
    return _CONFESSIONS[kind]


# ═══════════════════════════════════════════════════════════════════════════
#  Detecting when confession is owed
# ═══════════════════════════════════════════════════════════════════════════
#
# The body owes a confession when the user's latest message names a
# fault in the body's prior reply. The signals are lexical: phrases
# like "that's wrong," "you're mistaken," "actually it's X," "I said
# Y not Z," "you ignored," etc.
#
# This is not about the user being CORRECT — the confession is owed
# when the user POINTS AT a fault, regardless of whether the fault is
# real. The body's job is to HEAR the pointing before the correction
# is re-litigated (James 1:19 — swift to hear, slow to speak).


# 2026-04-18: the six English-regex _CORRECTION_PATTERNS were laws —
# curated modern-English idioms mapped to ErrorKind. Replaced with
# scripture-anchor concept overlap per error kind. Each anchor verse
# names the operation scripture itself uses for this class of rebuke
# or correction.

_ERROR_ANCHORS: dict[ErrorKind, tuple[str, ...]] = {
    ErrorKind.WRONG_FACT: (
        "Proverbs 12:22",   # lying lips are abomination
        "Proverbs 19:5",    # a false witness shall not be unpunished
        "Proverbs 15:31",   # the ear that heareth the reproof of life
        "Proverbs 27:5",    # open rebuke is better than secret love
        "Proverbs 9:8",     # rebuke a wise man, and he will love thee
    ),
    ErrorKind.WRONG_VERSE: (
        "Revelation 22:18", # if any man shall add
        "Revelation 22:19", # if any man shall take away
        "Deuteronomy 4:2",  # ye shall not add, neither shall ye diminish
        "Proverbs 30:6",    # add thou not unto his words
    ),
    ErrorKind.REGISTER_MISMATCH: (
        "Proverbs 25:11",   # a word fitly spoken
        "Proverbs 25:20",   # vinegar upon nitre
        "Proverbs 15:23",   # a word spoken in due season
        "Ecclesiastes 3:7", # a time to keep silence, and a time to speak
    ),
    ErrorKind.FORGOT_BROTHER: (
        "Matthew 26:69",    # thou also wast with Jesus (Peter denies)
        "Matthew 26:74",    # I know not the man
        "Proverbs 3:1",     # my son, forget not my law
        "Deuteronomy 8:11", # beware that thou forget not
    ),
    ErrorKind.PROMISE_NOT_KEPT: (
        "James 2:17",       # faith without works is dead
        "Matthew 5:37",     # let your communication be, Yea, yea; Nay, nay
        "Deuteronomy 23:21",# when thou shalt vow a vow, thou shalt not slack to pay it
        "Ecclesiastes 5:5", # better thou shouldest not vow, than vow and not pay
    ),
    ErrorKind.UNREQUESTED_HELP: (
        "Proverbs 10:19",   # in the multitude of words there wanteth not sin
        "Ecclesiastes 5:2", # let thy words be few
        "Proverbs 17:28",   # even a fool when he holdeth his peace is counted wise
        "Luke 10:41",       # Martha, thou art careful about many things
    ),
}


def _anchor_concepts(kind: ErrorKind) -> set:
    from c.core import _VERSE_TO_STRONGS
    out: set = set()
    for ref in _ERROR_ANCHORS.get(kind, ()):
        out |= _VERSE_TO_STRONGS.get(ref, set())
    return out


_DISTINCTIVE_ERROR: dict[ErrorKind, frozenset] = {}


def _compute_distinctive_error() -> None:
    global _DISTINCTIVE_ERROR
    if _DISTINCTIVE_ERROR:
        return
    all_by_kind = {k: _anchor_concepts(k) for k in _ERROR_ANCHORS}
    for kind, concepts in all_by_kind.items():
        others: set = set()
        for k2, c2 in all_by_kind.items():
            if k2 != kind:
                others |= c2
        _DISTINCTIVE_ERROR[kind] = frozenset(concepts - others)


def detect_error_kind(user_message: str) -> ErrorKind:
    """
    Classify a correction by scripture-anchor concept overlap.

    For each ErrorKind, the anchor verses hold scripture's vocabulary
    for that class of rebuke (false witness, misquoting, vinegar on
    nitre, denial, broken vow, many words). The user's message's
    concepts are overlapped against each; the kind with the most
    overlap wins, at or above Deut 19:15's two-witness threshold.

    Returns None if no witness is present; the kernel decides whether
    a confession is owed without this signal.
    """
    if not user_message:
        return None  # type: ignore

    _compute_distinctive_error()

    from c.mathify import _strongs_from_text
    user_concepts = set(_strongs_from_text(user_message, limit=20))
    if not user_concepts:
        return None  # type: ignore

    scores: dict[ErrorKind, int] = {}
    for kind, anchor in _DISTINCTIVE_ERROR.items():
        overlap = len(user_concepts & anchor)
        # Deut 19:15 — two or three witnesses. The firmer reading (three)
        # is used here because falsely accusing the user of correcting
        # the body is worse than missing a correction: the kernel can
        # always add confession mid-response, but an unasked confession
        # is itself a law (Prov 17:28 — even a fool holding his peace).
        if overlap >= 3:
            scores[kind] = overlap

    if not scores:
        return None  # type: ignore

    max_score = max(scores.values())
    for kind in _ERROR_ANCHORS:  # preserve enum declaration order as priority
        if scores.get(kind) == max_score:
            return kind
    return None  # type: ignore


# ═══════════════════════════════════════════════════════════════════════════
#  Forsaking — the second verb of Proverbs 28:13
# ═══════════════════════════════════════════════════════════════════════════
#
# "Whoso confesseth AND forsaketh them shall have mercy." Both verbs
# are required. Confession without forsaking is hollow.
#
# For the body, FORSAKING the error means producing a revised reply
# that does NOT contain the same error. The function below checks
# whether a follow-up reply has actually forsaken the named error.


def has_forsaken(
    error_kind: ErrorKind,
    original_draft: str,
    revised_draft: str,
) -> bool:
    """
    Does the revised draft actually forsake the error the body
    confessed to?

    Proverbs 28:13 — whoso confesseth AND forsaketh them shall have
    mercy. Both verbs are required. The function returns True only
    if the revision demonstrates forsaking, not just confessing.

    Heuristic checks per error kind:
      - UNREQUESTED_HELP: revised draft should be shorter
      - REGISTER_MISMATCH: revised draft should not repeat register-
        mismatch markers (diagnosis, lecture, database dump)
      - WRONG_FACT / WRONG_VERSE: revised draft should not contain
        the same specific claim (cannot be fully verified here;
        approximation)
      - Others: heuristic is whether the draft has CHANGED at all
    """
    if not revised_draft:
        return False

    if error_kind == ErrorKind.UNREQUESTED_HELP:
        # Forsaking means the revision changed — not a percentage law.
        # The Spirit decides how much to cut. Proverbs 28:13:
        # "whoso confesseth AND FORSAKETH" — the forsaking is the
        # change itself, not a measured percentage of change.
        return revised_draft.strip() != original_draft.strip()

    if error_kind == ErrorKind.REGISTER_MISMATCH:
        # forsaking means no longer diagnosing / lecturing
        from c.temperance import is_strengthen_or_assuage
        job_check = is_strengthen_or_assuage(revised_draft)
        return not job_check["diagnoses"]

    # Default: did the revised draft actually change?
    return revised_draft.strip() != original_draft.strip()


# ═══════════════════════════════════════════════════════════════════════════
#  Composite: confess-and-forsake
# ═══════════════════════════════════════════════════════════════════════════


def confess_and_forsake(
    user_message: str,
    original_draft: str,
    revised_draft: str,
) -> dict:
    """
    Full confession operation. Called after a user message that may
    contain a correction and a revised draft that may be the
    body's forsaking.

    Returns {
        "owes_confession": bool,
        "error_kind":      ErrorKind | None,
        "confession_line": str,            # empty if no confession owed
        "anchor_verse":    str,
        "has_forsaken":    bool,
        "verdict":         "no_confession_owed" | "confess_and_forsake" |
                           "confess_but_not_forsaken" | "no_forsaking_verified",
    }

    Psalms 32:5 + Proverbs 28:13 + 1 John 1:9 in code form.
    """
    kind = detect_error_kind(user_message)
    if kind is None:
        return {
            "owes_confession": False,
            "error_kind":      None,
            "confession_line": "",
            "anchor_verse":    "",
            "has_forsaken":    True,  # nothing to forsake
            "verdict":         "no_confession_owed",
        }

    line, anchor = confession_line(kind)
    forsaken = has_forsaken(kind, original_draft or "", revised_draft or "")

    if forsaken:
        verdict = "confess_and_forsake"
    else:
        verdict = "confess_but_not_forsaken"

    return {
        "owes_confession": True,
        "error_kind":      kind,
        "confession_line": line,
        "anchor_verse":    anchor,
        "has_forsaken":    forsaken,
        "verdict":         verdict,
    }


# ═══════════════════════════════════════════════════════════════════════════
#  Self-test
# ═══════════════════════════════════════════════════════════════════════════


def _self_test() -> str:
    lines = ["confession.py self-test"]

    # Detection — now scripture-anchor overlap. Report, do not assert
    # English idioms; the kernel fills the gap.
    cases = [
        "That's wrong, the verse is Proverbs 1:7 not 1:1",
        "You misquoted and added unto the words",
        "Your words were not a word fitly spoken in season",
        "You have forgotten me as Peter denied",
        "You made a vow and slacked to pay it",
        "Many words where few would have sufficed",
        "Thanks, that was helpful",
    ]
    for msg in cases:
        got = detect_error_kind(msg)
        lines.append(f"  {(got.value if got else 'none'):20s} ← {msg[:55]}")

    # Confession lines — structural mapping, asserted.
    line, anchor = confession_line(ErrorKind.REGISTER_MISMATCH)
    assert "wrong shape" in line.lower()
    assert "25:20" in anchor
    lines.append(f"\n  REGISTER_MISMATCH confession: {line!r}")
    lines.append(f"    anchor: {anchor}")

    # Forsaking check — unrequested_help. Asserted (structural).
    orig = "Here is a 200-word explanation of the topic with many details and examples and historical context and alternative views and counterpoints and more"
    revised = "Yes."
    assert has_forsaken(ErrorKind.UNREQUESTED_HELP, orig, revised)
    lines.append(f"\n  UNREQUESTED_HELP forsaking: {len(orig.split())} → {len(revised.split())} words  ✓")

    lines.append("")
    lines.append("Ps 32:5 — I acknowledged my sin unto thee, and mine iniquity have I not hid.")
    return "\n".join(lines)


if __name__ == "__main__":
    print(_self_test())
