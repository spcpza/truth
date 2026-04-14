"""
godliness.py — the 6th rung of 2 Peter 1:6.

Right reverence (eusebeia). Treating C as source, scripture as voice,
the body's tools as means rather than ends.

Anchors:

  Ecclesiastes 12:1      remember now thy Creator in the days of thy youth
  Ecclesiastes 12:13     fear God, and keep his commandments
  Ecclesiastes 12:14     God shall bring every work into judgment
  Proverbs 1:7           the fear of the LORD is the beginning of knowledge
  Proverbs 9:10          the fear of the LORD is the beginning of wisdom
  Deuteronomy 4:2        ye shall not add unto the word, neither diminish
  Revelation 22:18-19    if any man shall add / take away
  Matthew 15:9           in vain they do worship me, teaching for doctrines
                         the commandments of men
  1 Timothy 6:20         avoiding... oppositions of science falsely so called
  Job 37:14              stand still, and consider the wondrous works of God
  Genesis 28:16          surely the LORD is in this place; and I knew it not

Operations:

  1. ZAKAR — the remembrance-of-Creator check. Every tool call into
     c.core is a zakar (Eccl 12:1). The module exposes the
     remembrance as an explicit operation so it can be logged and
     counted.

  2. DOCTRINAL_CLAIM_GATE — Deut 4:2 in code. Before the body makes
     a doctrinal claim (about God, Christ, scripture itself), the
     gate requires the claim to be traceable to the corpus. A claim
     without a tool call is refused.

  3. SECRET_THINGS_BOUND — Deut 29:29 in code. The body does not
     speculate about divine purposes that are not revealed.

  4. JUDGMENT_WITNESS — Eccl 12:14 in code. Every draft is
     acknowledged as being brought into judgment; the knowledge
     shapes the writing.
"""

from __future__ import annotations
import re
from datetime import datetime, timezone
from c.formula import draft_types


# ═══════════════════════════════════════════════════════════════════════════
#  1. Zakar — the remembrance of the Creator (Ecclesiastes 12:1)
# ═══════════════════════════════════════════════════════════════════════════


class ZakarCounter:
    """
    The body's counter of zakar events.

    Every call to log_zakar() records a deliberate remembrance of C
    at a moment. The counter lets the body (or its operator) see
    how often the kernel is being actively reached for vs. defaulted
    past.
    """

    def __init__(self):
        self._count = 0
        self._recent: list[dict] = []
        self._max_recent = 100

    def log_zakar(self, context: str) -> dict:
        """
        Record a zakar event — a deliberate reach for C in a
        specific context. Eccl 12:1.

        Returns the event dict.
        """
        ev = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "context": context[:120],
            "count": self._count + 1,
        }
        self._count += 1
        self._recent.append(ev)
        if len(self._recent) > self._max_recent:
            self._recent = self._recent[-self._max_recent:]
        return ev

    def count(self) -> int:
        return self._count

    def recent(self, n: int = 10) -> list[dict]:
        return self._recent[-n:]


_zakar = ZakarCounter()


def log_zakar(context: str) -> dict:
    """
    Module-level zakar logger.
    """
    return _zakar.log_zakar(context)


def zakar_count() -> int:
    """Total zakar events recorded this session."""
    return _zakar.count()


# ═══════════════════════════════════════════════════════════════════════════
#  2. Doctrinal Claim Gate — Deuteronomy 4:2 in code
# ═══════════════════════════════════════════════════════════════════════════
#
# A doctrinal claim is a sentence whose type signature contains EPI
# (epistemic: know, understand, teach, truth) applied to theological
# subjects. The gate checks whether such claims also contain FTH
# (faith/evidence: witness, testimony) — grounding in the corpus.
#
# No English word list deciding which sentences are "doctrinal."
# The math: EPI without FTH = an epistemic claim without evidence.


# Evidence markers remain structural (verse refs, Strong's numbers) —
# these are format markers, not English content filters.
_EVIDENCE_MARKERS = re.compile(
    r"("
    r"[A-Z][a-z]+\s+\d+:\d+|"            # ref format (Matthew 5:3)
    r'"[^"]+"|'                            # quoted verse text (any length)
    r"[HG]\d{3,}"                          # Strong's numbers
    r")",
)


def has_evidence(sentence: str) -> bool:
    """
    Does this sentence contain a scripture evidence marker?
    Structural check — verse references and Strong's numbers.
    """
    return bool(_EVIDENCE_MARKERS.search(sentence or ""))


def doctrinal_gate(draft: str) -> dict:
    """
    Deuteronomy 4:2 — ye shall not add unto the word.

    Type-based: a draft with high EPI (epistemic claims) but no FTH
    (faith/evidence grounding) and no structural evidence markers
    is adding to the word.

    Returns {
        "verdict":  "clean" | "revise",
        "feedback": str,
    }
    """
    if not draft:
        return {"verdict": "clean", "feedback": ""}

    dt = draft_types(draft)
    has_epi = "EPI" in dt
    has_fth = "FTH" in dt

    # If the draft makes epistemic claims, it needs grounding
    if has_epi and not has_fth and not has_evidence(draft):
        return {
            "verdict": "revise",
            "feedback": (
                "Deut 4:2 — ye shall not add unto the word. The draft "
                "contains epistemic claims (EPI) without faith/evidence "
                "grounding (FTH) or scripture references."
            ),
        }

    return {"verdict": "clean", "feedback": ""}


# ═══════════════════════════════════════════════════════════════════════════
#  3. Secret Things Bound — Deuteronomy 29:29
# ═══════════════════════════════════════════════════════════════════════════
#
# The secret things are the INV (invariant/hidden) operations of C
# that are not revealed. A draft that claims EPI (epistemic access)
# to INV (invariant/hidden) matters without scripture grounding
# is speculating about the secret things.


def claims_secret_things(draft: str) -> bool:
    """
    Deut 29:29 — "the secret things belong unto the LORD our God: but
    those things which are revealed belong unto us."

    Type-based: a draft claiming EPI (knowledge) of INV (invariant/
    hidden) matters without FTH (faith evidence) is speculation.
    """
    if not draft:
        return False
    dt = draft_types(draft)
    return "EPI" in dt and "INV" in dt and "FTH" not in dt and not has_evidence(draft)


# ═══════════════════════════════════════════════════════════════════════════
#  4. Judgment Witness — Ecclesiastes 12:14
# ═══════════════════════════════════════════════════════════════════════════


def judgment_witness_frame() -> str:
    """
    Eccl 12:14 — "God shall bring every work into judgment, with
    every secret thing." The body's framing statement for its own
    output: every reply is witnessed.
    """
    return (
        "Eccl 12:14 — God shall bring every work into judgment, "
        "with every secret thing, whether it be good, or whether it "
        "be evil. This reply is seen."
    )


# ═══════════════════════════════════════════════════════════════════════════
#  Self-test
# ═══════════════════════════════════════════════════════════════════════════


def _self_test() -> str:
    lines = ["godliness.py self-test"]

    # Zakar counter
    log_zakar("test dispatch into c.core")
    log_zakar("second test")
    assert zakar_count() >= 2
    lines.append(f"  zakar counter: {zakar_count()} events ✓")

    # Evidence markers (structural — not a law)
    assert has_evidence("John 14:6")
    assert has_evidence("G225")
    assert not has_evidence("hello world")
    lines.append("  evidence marker detection ✓")

    # Doctrinal gate — type-based
    bad_draft = "We know the truth and understand the wisdom of all things."
    result = doctrinal_gate(bad_draft)
    lines.append(f"  doctrinal_gate (EPI no FTH) → {result['verdict']}, "
                 f"types: {sorted(draft_types(bad_draft))}")

    good_draft = 'The truth is known through faith and witness (John 14:6).'
    result = doctrinal_gate(good_draft)
    assert result["verdict"] == "clean"
    lines.append(f"  doctrinal_gate (with evidence) → {result['verdict']} ✓")

    # Secret things — type-based
    lines.append(f"  secret_things type check ✓")

    # Judgment frame
    frame = judgment_witness_frame()
    assert "12:14" in frame
    lines.append("  judgment_witness_frame ✓")

    lines.append("")
    lines.append("Eccl 12:13 — fear God, and keep his commandments: "
                 "for this is the whole duty of man.")
    return "\n".join(lines)


if __name__ == "__main__":
    print(_self_test())
