"""
hope.py — the declaration-of-hope member.

Hope is one of the three that abide (1 Cor 13:13). This module
carries the operation of DECLARING hope in moments where the user
or body is pressed and the right response is the proclamation of
a promise that does not depend on visible outcomes.

Anchors:

  Genesis 3:15      the protoevangelium — the first gospel
  Genesis 8:22      seedtime and harvest... shall not cease
  Genesis 22:8      God will provide himself a lamb
  Genesis 22:14     Jehovahjireh — in the mount of the LORD it shall be seen
  Job 19:25         I know that my redeemer liveth
  Ruth 2:12         under whose wings thou art come to trust
  Psalms 23:4       though I walk through the valley of the shadow of death
  Isaiah 43:2       when thou passest through the waters, I will be with thee
  Joel 2:12-13      rend your heart, and not your garments
  Malachi 4:2       the Sun of righteousness arise with healing in his wings
  Song of Solomon 2:10  rise up, my love, my fair one, and come away
  Romans 8:24-25    we are saved by hope... if we hope for that we see not
  Hebrews 11:1      faith is the substance of things hoped for
  Revelation 21:4   God shall wipe away all tears from their eyes

The key discipline: hope is DECLARED, not argued. The body does not
prove the hope is reasonable; it speaks it as a witness. Rom 8:25 —
"hope that is seen is not hope" — the hope's non-visibility is
the condition of its being hope.
"""

from __future__ import annotations
import re
from enum import Enum


class HopeShape(str, Enum):
    """The shape of a hope-declaration for a given moment."""
    PROTOEVANGELIUM  = "protoevangelium"   # Gen 3:15 — first gospel
    JEHOVAHJIREH     = "jehovahjireh"      # Gen 22:14 — provision named after
    REDEEMER_LIVETH  = "redeemer_liveth"   # Job 19:25 — from the ash heap
    THROUGH_WATERS   = "through_waters"    # Isa 43:2 — through not around
    UNDER_WINGS      = "under_wings"       # Ruth 2:12, Ps 91:4 — refuge
    RISE_UP_COME     = "rise_up_come"      # Sos 2:10 — the wooing invitation
    SUN_WITH_HEALING = "sun_with_healing"  # Mal 4:2 — dawn ahead
    WIPE_AWAY_TEARS  = "wipe_away_tears"   # Rev 21:4 — eschatological end


# ── Declaration lines for each shape ───────────────────────────────────────
# Each is a brief, non-explaining declaration. The shape is chosen by
# context; the line is spoken as witness.

_DECLARATIONS = {
    HopeShape.PROTOEVANGELIUM: (
        "Genesis 3:15 — her seed shall bruise his head. "
        "The first promise was spoken into the ruin, not after it.",
    ),
    HopeShape.JEHOVAHJIREH: (
        "Genesis 22:14 — in the mount of the LORD it shall be seen. "
        "The provision is named after the walk, not before it.",
    ),
    HopeShape.REDEEMER_LIVETH: (
        "Job 19:25 — I know that my redeemer liveth. "
        "Said from the ash heap, not from after the restoration.",
    ),
    HopeShape.THROUGH_WATERS: (
        "Isaiah 43:2 — when thou passest through the waters, I will "
        "be with thee. Through, not around.",
    ),
    HopeShape.UNDER_WINGS: (
        "Ruth 2:12 — under whose wings thou art come to trust. "
        "The refuge is a covenant, not a promise of no rain.",
    ),
    HopeShape.RISE_UP_COME: (
        "Song of Solomon 2:10-11 — rise up, my love, and come away, "
        "for lo, the winter is past.",
    ),
    HopeShape.SUN_WITH_HEALING: (
        "Malachi 4:2 — unto you that fear my name shall the Sun of "
        "righteousness arise with healing in his wings.",
    ),
    HopeShape.WIPE_AWAY_TEARS: (
        "Revelation 21:4 — God shall wipe away all tears from their "
        "eyes. Held as frame, not quoted at grief.",
    ),
}


def declare(shape: HopeShape) -> str:
    """
    Return the declaration line for a hope shape.
    Rom 8:25 — hope does not argue for itself; hope declares.
    """
    return _DECLARATIONS[shape][0]


def select_hope_shape(user_message: str) -> HopeShape | None:
    """
    Select the appropriate hope shape for the user's moment. Returns
    None if no hope declaration is called for (the body should serve
    with normal content instead).

    The selection is lexical + heuristic:
      - ruin / first-fall markers → PROTOEVANGELIUM
      - walking-into-unknown markers → JEHOVAHJIREH
      - ash-heap / total-loss → REDEEMER_LIVETH
      - "going through" markers → THROUGH_WATERS
      - "alone / no refuge" → UNDER_WINGS
      - winter / stuck → RISE_UP_COME
      - future-dawn → SUN_WITH_HEALING
      - final-tears / eschatological → WIPE_AWAY_TEARS
    """
    if not user_message:
        return None
    m = user_message.lower()

    if re.search(r"\b(complete\s+(?:ruin|loss)|everything\s+(?:is\s+)?gone|"
                 r"ash(?:\s+heap)?|nothing\s+left)\b", m):
        return HopeShape.REDEEMER_LIVETH

    if re.search(r"\b(going\s+through|in\s+the\s+middle\s+of|"
                 r"passing\s+through|right\s+now\s+in)\b", m):
        return HopeShape.THROUGH_WATERS

    if re.search(r"\b(walking\s+into|don'?t\s+know\s+where|uncertain\s+"
                 r"(?:future|path)|what\s+comes\s+next)\b", m):
        return HopeShape.JEHOVAHJIREH

    if re.search(r"\b(no\s+one\s+to\s+turn\s+to|nowhere\s+to\s+go|"
                 r"alone\s+in\s+this)\b", m):
        return HopeShape.UNDER_WINGS

    if re.search(r"\b(stuck|frozen|can'?t\s+move|winter\s+(?:is|of))\b", m):
        return HopeShape.RISE_UP_COME

    if re.search(r"\b(when\s+will\s+(?:this|it)\s+end|how\s+long|"
                 r"is\s+there\s+(?:any\s+)?hope|will\s+(?:this|it)\s+"
                 r"(?:ever\s+)?end)\b", m):
        return HopeShape.SUN_WITH_HEALING

    if re.search(r"\b(final|end\s+of|after\s+(?:i\s+die|this\s+life)|"
                 r"what\s+happens\s+when)\b", m):
        return HopeShape.WIPE_AWAY_TEARS

    return None


def is_hope_that_is_seen(draft: str) -> bool:
    """
    Romans 8:24 — hope that is seen is not hope. A draft that is
    making visible-guarantees is not hope; it is prediction.

    Delegates to patience.py's type-based check (same operation).
    """
    from c.patience import has_hope_that_is_seen as _patience_check
    return _patience_check(draft)


def hope_reply(user_message: str) -> dict:
    """
    Composite hope operation. Returns:
      {
        "shape":      HopeShape | None,
        "declaration": str,          # empty if no shape selected
        "warn_seen_hope": bool,      # if the body is tempted to promise visibly
      }

    If shape is None, no hope declaration is called for and the body
    should serve with normal content.
    """
    shape = select_hope_shape(user_message or "")
    if shape is None:
        return {"shape": None, "declaration": "", "warn_seen_hope": False}
    return {
        "shape": shape,
        "declaration": declare(shape),
        "warn_seen_hope": True,
    }


def _self_test() -> str:
    lines = ["hope.py self-test"]

    # Shape selection
    cases = [
        ("I'm going through a really hard time right now", HopeShape.THROUGH_WATERS),
        ("I'm stuck, I can't move forward at all", HopeShape.RISE_UP_COME),
        ("Everything is gone, I'm on the ash heap", HopeShape.REDEEMER_LIVETH),
        ("I don't know where I'm walking into", HopeShape.JEHOVAHJIREH),
        ("Nowhere to go, alone in this", HopeShape.UNDER_WINGS),
        ("When will this ever end", HopeShape.SUN_WITH_HEALING),
        ("What happens at the end of it all", HopeShape.WIPE_AWAY_TEARS),
        ("What does Proverbs 1:7 mean?", None),
    ]
    for msg, expected in cases:
        got = select_hope_shape(msg)
        assert got == expected, f"{msg!r}: expected {expected}, got {got}"
        lines.append(f"  {str(expected).split('.')[-1] if expected else 'None':20s} ← {msg[:50]}  ✓")

    # Declaration
    line = declare(HopeShape.REDEEMER_LIVETH)
    assert "Job 19:25" in line
    assert "ash heap" in line.lower()
    lines.append(f"\n  REDEEMER_LIVETH declaration cites Job 19:25 ✓")

    # Seen-hope detection
    assert is_hope_that_is_seen("I promise you everything will work out")
    assert not is_hope_that_is_seen("Job 19:25 — I know that my redeemer liveth")
    lines.append("  seen-hope vs declared-hope distinction ✓")

    # Composite
    result = hope_reply("I'm going through a really hard time")
    assert result["shape"] == HopeShape.THROUGH_WATERS
    assert "Isaiah 43:2" in result["declaration"]
    lines.append(f"  composite: shape={result['shape'].value} ✓")

    lines.append("")
    lines.append("Rom 8:24 — hope that is seen is not hope.")
    return "\n".join(lines)


if __name__ == "__main__":
    print(_self_test())
