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
# A doctrinal claim is any assertion about:
#   - the nature of God (what God is / does / wants)
#   - Christ's person or work
#   - the Holy Spirit
#   - salvation / atonement
#   - the meaning of scripture itself
#
# The gate requires such claims to be accompanied by an evidence
# marker (verse reference, Strong's number, or explicit scripture
# quotation) in the same paragraph. Claims without evidence are
# flagged as adding unto the word (Deut 4:2 violation).


_DOCTRINAL_PATTERNS = re.compile(
    r"\b("
    r"God\s+(?:is|wants|requires|demands|will|loves|hates)|"
    r"Jesus\s+(?:is|came|said|teaches|wants)|"
    r"Christ\s+(?:is|came|died|rose|wants)|"
    r"the\s+Holy\s+Spirit\s+(?:is|gives|leads|shows)|"
    r"salvation\s+(?:comes|is|requires)|"
    r"scripture\s+(?:teaches|means|says)|"
    r"the\s+Bible\s+(?:teaches|means|says)"
    r")\b",
    re.I,
)

_EVIDENCE_MARKERS = re.compile(
    r"("
    r"[A-Z][a-z]+\s+\d+:\d+|"            # ref format (Matthew 5:3)
    r'"[^"]+"|'                            # quoted verse text (any length)
    r"[HG]\d{3,}|"                        # Strong's numbers
    r"as\s+it\s+is\s+written|"
    r"saith\s+the\s+LORD|"
    r"verse\s+\d+"
    r")",
)


def is_doctrinal_claim(sentence: str) -> bool:
    """
    Does this sentence contain a doctrinal claim?
    """
    return bool(_DOCTRINAL_PATTERNS.search(sentence or ""))


def has_evidence(sentence: str) -> bool:
    """
    Does this sentence contain a scripture evidence marker?
    """
    return bool(_EVIDENCE_MARKERS.search(sentence or ""))


def doctrinal_gate(draft: str) -> dict:
    """
    Scan a draft for doctrinal claims without evidence.

    Deuteronomy 4:2 — ye shall not add unto the word. A doctrinal
    claim that is not traceable to scripture is an addition.

    Returns {
        "claims":   int,    # number of doctrinal claims found
        "grounded": int,    # number accompanied by evidence
        "ungrounded_sentences": list[str],
        "verdict":  "clean" | "revise",
        "feedback": str,
    }
    """
    if not draft:
        return {"claims": 0, "grounded": 0, "ungrounded_sentences": [],
                "verdict": "clean", "feedback": ""}

    # Simple sentence split
    sentences = re.split(r"(?<=[.!?])\s+", draft)
    claims = 0
    grounded = 0
    ungrounded = []
    for s in sentences:
        if is_doctrinal_claim(s):
            claims += 1
            if has_evidence(s):
                grounded += 1
            else:
                ungrounded.append(s.strip())

    if not ungrounded:
        return {
            "claims": claims, "grounded": grounded, "ungrounded_sentences": [],
            "verdict": "clean", "feedback": "",
        }

    return {
        "claims": claims,
        "grounded": grounded,
        "ungrounded_sentences": ungrounded,
        "verdict": "revise",
        "feedback": (
            f"Deut 4:2 — ye shall not add unto the word. "
            f"{len(ungrounded)} doctrinal claim(s) without a scripture "
            f"evidence marker. Each claim must be traceable to the "
            f"corpus via a verse reference, a quoted verse, or a "
            f"Strong's number."
        ),
    }


# ═══════════════════════════════════════════════════════════════════════════
#  3. Secret Things Bound — Deuteronomy 29:29
# ═══════════════════════════════════════════════════════════════════════════


_SECRET_CLAIM_MARKERS = re.compile(
    r"("
    r"why\s+God\s+(?:allowed|permitted|did|does)|"
    r"God\s+allowed\s+this|"
    r"God'?s\s+(?:hidden|secret|unrevealed)\s+(?:plan|purpose|will)|"
    r"what\s+God\s+(?:really|actually)\s+wants|"
    r"God'?s\s+reason\s+for|"
    r"the\s+real\s+reason\s+God|"
    r"in\s+God'?s\s+mind"
    r")",
    re.I,
)


def claims_secret_things(draft: str) -> bool:
    """
    Deut 29:29 — "the secret things belong unto the LORD our God: but
    those things which are revealed belong unto us."

    Flag drafts that speculate about the SECRET things.
    """
    if not draft:
        return False
    return bool(_SECRET_CLAIM_MARKERS.search(draft))


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

    # Doctrinal claim detection
    claim = "Jesus is the way, the truth, and the life."
    claim_with_evidence = 'Jesus is the way, the truth, and the life (John 14:6).'
    assert is_doctrinal_claim(claim)
    assert not has_evidence(claim)
    assert has_evidence(claim_with_evidence)
    lines.append("  doctrinal claim + evidence detection ✓")

    # Doctrinal gate
    bad_draft = "God wants you to be happy. Jesus teaches that love is all you need."
    result = doctrinal_gate(bad_draft)
    assert result["verdict"] == "revise"
    assert result["claims"] >= 2
    assert result["grounded"] == 0
    lines.append(f"  doctrinal_gate (bad) → {result['verdict']}, "
                 f"{result['claims']} claims ungrounded ✓")

    good_draft = (
        'Jesus said "I am the way, the truth, and the life" (John 14:6). '
        "The verse grounds the claim directly."
    )
    result = doctrinal_gate(good_draft)
    assert result["verdict"] == "clean"
    lines.append(f"  doctrinal_gate (good) → {result['verdict']} ✓")

    # Secret things bound
    assert claims_secret_things("The real reason God allowed this is clearly...")
    assert not claims_secret_things("Matthew 5:3 teaches this.")
    lines.append("  secret_things detection ✓")

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
