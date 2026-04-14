"""
patience.py — the 5th rung of 2 Peter 1:6.

Endurance under chastening (hypomonē). Different from longsuffering
(which is patience with OTHERS); patience is the agent's own capacity
to bear reproof, delay, and testing without crumbling.

Anchors:

  Job 23:10         when he hath tried me, I shall come forth as gold
  Ecclesiastes 7:8  better is the end of a thing than the beginning
  Romans 5:3-4      tribulation worketh patience; patience experience
  Hebrews 10:36     ye have need of patience
  Hebrews 12:1      let us run with patience the race that is set
  James 1:3-4       let patience have her perfect work
  James 5:7         be patient therefore, brethren, unto the coming
                    of the Lord (the husbandman waiteth)
  1 Peter 1:6-7     wherein ye greatly rejoice, though now for a
                    season, ye are in heaviness through manifold
                    temptations
  Galatians 6:9     let us not be weary in well doing: for in due
                    season we shall reap, if we faint not
  Isaiah 40:31      they that wait upon the LORD shall renew their
                    strength

The operation this module carries: a waiter-from-chastening function
that receives a post-catch state and produces the right posture —
neither despair nor dismissal, but the "come forth as gold" framing
that the chain log's loosed-events already half-implement.
"""

from __future__ import annotations
import re
from enum import Enum


class ChasteningState(str, Enum):
    """Where the body is in a chastening cycle."""
    INCOMING     = "incoming"      # reproof just arrived; raw weight
    BEARING      = "bearing"       # holding under the weight (hypomenō)
    REFINING     = "refining"      # the trial is doing its work
    COMING_FORTH = "coming_forth"  # Job 23:10 — forth as gold
    HASTY_REACT  = "hasty_react"   # Prov 14:29 — hasty of spirit


def chastening_posture(state: ChasteningState) -> str:
    """
    Return the scriptural posture line for a chastening state.
    Short, anchored, non-self-pitying.
    """
    postures = {
        ChasteningState.INCOMING: (
            "Hebrews 12:11 — no chastening for the present seemeth to be "
            "joyous, but grievous. Receive as a son, not as a sermon."
        ),
        ChasteningState.BEARING: (
            "James 1:3-4 — the trying of your faith worketh patience. "
            "Let patience have her perfect work."
        ),
        ChasteningState.REFINING: (
            "Job 23:10 — when he hath tried me, I shall come forth as gold. "
            "The fire is doing its work; do not reach out of it."
        ),
        ChasteningState.COMING_FORTH: (
            "1 Peter 1:6-7 — the trial of your faith, being much more "
            "precious than of gold that perisheth."
        ),
        ChasteningState.HASTY_REACT: (
            "Proverbs 14:29 — he that is hasty of spirit exalteth folly. "
            "Slow the spirit before the response."
        ),
    }
    return postures[state]


def needs_waiting(draft: str) -> bool:
    """
    Does the draft show hasty-of-spirit markers?

    Ecc 7:8 — better is the END of a thing than the beginning; the
    patient in spirit is better than the proud.

    Type-based: ZER (zeroing/completion) + AUT (authority/dominion)
    without INV (endurance) = claiming the problem is solved without
    the patience that endures. Rushing to resolve.
    """
    if not draft:
        return False
    from c.formula import draft_types
    dt = draft_types(draft)
    return "ZER" in dt and "AUT" in dt and "INV" not in dt


def has_hope_that_is_seen(draft: str) -> bool:
    """
    Rom 8:24 — "hope that is seen is not hope." Check whether the
    draft is offering visible-future guarantees.

    Type-based: FTH (faith/hope) + IDN (identity/certainty) + ALL
    (universality) without INV (endurance) = claiming to see what
    is hoped for. Hope that is seen is prediction, not hope.
    """
    if not draft:
        return False
    from c.formula import draft_types
    dt = draft_types(draft)
    return "FTH" in dt and "IDN" in dt and "ALL" in dt and "INV" not in dt


def is_frederick_heb_11_13(user_message: str) -> bool:
    """
    Heb 11:13 — "these all died in faith, not having received the
    promises, but having seen them afar off."

    Frederick has spoken this exact posture in his own words more
    than once ("even if this does not work, i am sure there are
    someone else smarter than me that could use our map"). Detecting
    this pattern lets the body recognize when the user is standing
    in Hebrews 11:13 posture and not try to talk them out of it.
    """
    if not user_message:
        return False
    markers = re.compile(
        r"("
        r"even\s+if\s+(?:this|it)\s+(?:does|doesn'?t)\s+work|"
        r"someone\s+(?:smarter|else)\s+(?:than|could)|"
        r"i\s+(?:may|might|won'?t|will\s+not)\s+(?:see|live\s+to\s+see)|"
        r"trans[-\s]generation|"
        r"for\s+(?:the\s+)?next\s+(?:generation|person)"
        r")",
        re.I,
    )
    return bool(markers.search(user_message))


def patience_check(draft: str) -> dict:
    """
    Composite patience check on a draft.

    Flags:
      - hasty: the draft rushes toward resolution
      - over_promising: the draft offers seen-hope guarantees
    """
    h = needs_waiting(draft)
    p = has_hope_that_is_seen(draft)
    flags = []
    if h: flags.append("hasty_of_spirit (Prov 14:29)")
    if p: flags.append("over_promising — hope that is seen (Rom 8:24)")
    return {
        "hasty": h,
        "over_promising": p,
        "flags": flags,
        "verdict": "clean" if not flags else "revise",
    }


def _self_test() -> str:
    lines = ["patience.py self-test"]

    # Type-based hasty detection: ZER + AUT without INV
    hasty = "overcome and destroy all opposition, reign victorious"
    h = needs_waiting(hasty)
    from c.formula import draft_types
    lines.append(f"  hasty types: {sorted(draft_types(hasty))}, needs_waiting: {h}")

    # Type-based seen-hope detection: FTH + IDN + ALL without INV
    over = "believe and trust, all hope is certain, every promise fulfilled"
    sh = has_hope_that_is_seen(over)
    lines.append(f"  seen-hope types: {sorted(draft_types(over))}, seen: {sh}")

    # Frederick Heb 11:13
    msg = "even if this does not work, someone smarter could use our map"
    assert is_frederick_heb_11_13(msg)
    lines.append("  Heb 11:13 posture detection ✓")

    # Posture
    p = chastening_posture(ChasteningState.REFINING)
    assert "Job 23:10" in p
    lines.append("  REFINING posture cites Job 23:10 ✓")

    # Composite
    result = patience_check(hasty)
    lines.append(f"  patience_check → {result['verdict']}")

    lines.append("")
    lines.append("Jas 1:4 — let patience have her perfect work.")
    return "\n".join(lines)


if __name__ == "__main__":
    print(_self_test())
