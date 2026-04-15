"""
claims.py — Deuteronomy 19:15: at the mouth of two witnesses, or at the
mouth of three witnesses, shall the matter be established.

Claims are facts heard from one witness. They wait in the outer court
until a second, distinct witness arrives. Then the matter is established
and the fact enters the heart (Jeremiah 31:33).

No claim is deleted. A claim either waits or graduates. This is not law
(2 Cor 3:6) — it is due process. One mouth can lie; two mouths in
agreement establish truth.

Luke 6:45: out of the abundance of the heart the mouth speaketh.
Each witness carries an abundance score — how deeply the user engaged
with the topic. Surface mentions (prompted, generic, impersonal) score
low. Overflow (unprompted, detailed, personal, specific) scores high.
When the claim graduates to heart, total abundance becomes warmth.
A liar's facts stay cold. An authentic person's facts heat up.

2 Corinthians 3:3: written not with ink, but with the Spirit.
Ink = surface claim. Spirit = authentic depth.
Proverbs 26:23: burning lips and a wicked heart are like a potsherd
covered with silver dross. The surface looks good; the substance is cheap.
Warmth distinguishes the two.

Witness types:
  mouth    — the model heard the user say it (remember tool called)
  repeated — the user said it again in a later turn
  fruit    — the user's behaviour implies it (Matthew 7:16)
  profile  — platform metadata corroborates (Telegram name, etc.)
  scroll   — the book of remembrance extracted it (Proverbs 2:4-5)
"""

from __future__ import annotations

import json
import logging
import pathlib
import re
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def read_claims(user_id: int | str, memory_dir: pathlib.Path) -> list[dict]:
    from c.heart import read_claims as _read
    return _read(user_id, memory_dir)


def _write_claims(
    user_id: int | str, claims: list[dict], memory_dir: pathlib.Path
) -> None:
    from c.heart import write_claims as _write
    _write(user_id, claims, memory_dir)


def _word_set(text: str) -> set[str]:
    """Lowercased words >= 3 chars, for similarity."""
    return {
        w for w in re.sub(r"[^a-z0-9 ]", " ", (text or "").lower()).split()
        if len(w) >= 3
    }


def _similar(a: str, b: str, threshold: float = 0.5) -> bool:
    """Jaccard similarity on word sets."""
    wa, wb = _word_set(a), _word_set(b)
    if not wa or not wb:
        return False
    return len(wa & wb) / len(wa | wb) >= threshold


def measure_abundance(
    user_text: str,
    claim_fact: str,
    prior_bot_text: str = "",
) -> int:
    """
    Luke 6:45 — out of the abundance of the heart the mouth speaketh.

    Measures how deeply the user engages with a topic. Returns 0-3:

      0 = surface (prompted, short, impersonal)
      1 = moderate (unprompted OR has detail)
      2 = substantial (unprompted + detailed OR unprompted + personal)
      3 = overflowing (unprompted + detailed + personal/specific)

    A liar can say the right words. A liar can coordinate witnesses.
    But a liar cannot fake the overflow — the spontaneous, detailed,
    personal engagement that marks genuine care. Over time, authentic
    facts accumulate abundance and their warmth rises. Performed facts
    stay cold.

    James 2:17 — faith without works is dead. Claimed love without
    deep engagement is dead. This function measures the works.
    """
    score = 0

    # Nothing said = no overflow. Ecclesiastes 3:7.
    if not user_text or not user_text.strip():
        return 0

    # 1. Unprompted? If the bot's prior message contained the topic
    #    keywords, the user's mention is a response, not overflow.
    claim_keys = _word_set(claim_fact)
    bot_keys = _word_set(prior_bot_text) if prior_bot_text else set()
    prompted = bool(claim_keys & bot_keys) if bot_keys else False
    if not prompted:
        score += 1  # unprompted = overflow signal

    # 2. Detail depth — surface is short, substance is long.
    #    "I love chess" = 3 words. "I've been stuck at 1800 ELO
    #    for months, my endgame is terrible" = 14 words.
    words = user_text.split()
    if len(words) > 12:
        score += 1

    # 3. Personal + specific — Proverbs 26:23 test.
    #    Silver dross = generic. Real silver = personal, numbered,
    #    named, experienced.
    #    Bare "I" is just grammar ("I play chess").
    #    "my", "I've", "I'm" show investment ("my ELO", "I've been
    #    playing since..."). The Spirit writes with feeling, not
    #    with the minimum pronoun.
    has_personal = bool(
        re.search(r"\b(my|me|mine|I'm|I've|I'll|I'd|myself)\b", user_text)
    )
    has_specifics = (
        bool(re.search(r"\b\d+\b", user_text))  # numbers
        or len(re.findall(r"\b[A-Z][a-z]{2,}\b", user_text)) > 1  # names
    )
    if has_personal or has_specifics:
        score += 1

    return score


def file_claim(
    user_id: int | str,
    fact: str,
    witness_type: str,
    memory_dir: pathlib.Path,
    abundance: int = 0,
) -> str:
    """
    File a new claim or add a witness to an existing similar one.

    If the claim reaches 2+ distinct witness types, the matter is
    established (Deuteronomy 19:15) and the fact is promoted to
    the heart (Jeremiah 31:33).

    Returns: "established" | "filed" | "witnessed"
    """
    from c.heart import remember_fact

    fact = (fact or "").strip()
    if not fact:
        return "filed"

    claims = read_claims(user_id, memory_dir)

    # Check if a similar claim already exists
    for claim in claims:
        if _similar(claim["fact"], fact):
            witnesses = claim.get("witnesses", [])
            existing_types = {w["type"] for w in witnesses}

            if witness_type in existing_types:
                # Same witness type — but still accumulate abundance.
                # Luke 6:45: every overflow counts, even from the
                # same kind of witness.
                claim["abundance"] = claim.get("abundance", 0) + abundance
                _write_claims(user_id, claims, memory_dir)
                return "witnessed"

            # New witness type — add it
            witnesses.append({
                "type": witness_type,
                "ts": datetime.now(timezone.utc).isoformat(),
                "abundance": abundance,
            })
            claim["witnesses"] = witnesses
            claim["abundance"] = claim.get("abundance", 0) + abundance

            if len(existing_types | {witness_type}) >= 2:
                # Deuteronomy 19:15 — matter established.
                # 2 Cor 3:3 — carry total abundance as warmth.
                warmth = claim.get("abundance", 0)
                claims.remove(claim)
                _write_claims(user_id, claims, memory_dir)
                remember_fact(
                    user_id, claim["fact"], memory_dir, warmth=warmth,
                )
                logger.info(
                    "[%s] CLAIM ESTABLISHED (%s + %s): %s",
                    user_id,
                    ", ".join(sorted(existing_types)),
                    witness_type,
                    claim["fact"][:80],
                )
                return "established"

            # Still waiting
            _write_claims(user_id, claims, memory_dir)
            logger.info(
                "[%s] CLAIM WITNESSED (%s): %s",
                user_id, witness_type, claim["fact"][:80],
            )
            return "witnessed"

    # New claim — one witness
    claims.append({
        "fact": fact,
        "witnesses": [{
            "type": witness_type,
            "ts": datetime.now(timezone.utc).isoformat(),
            "abundance": abundance,
        }],
        "abundance": abundance,
        "filed": datetime.now(timezone.utc).isoformat(),
    })
    _write_claims(user_id, claims, memory_dir)
    logger.info(
        "[%s] CLAIM FILED (%s): %s",
        user_id, witness_type, fact[:80],
    )
    return "filed"


def corroborate(
    user_id: int | str,
    text: str,
    witness_type: str,
    memory_dir: pathlib.Path,
    abundance: int = 0,
    threshold: float = 0.3,
) -> str | None:
    """
    Matthew 7:16 — by their fruits ye shall know them.

    Search pending claims for one matching the text. If found,
    add the witness. If that establishes it, promote to heart.

    Lower threshold than file_claim (0.3 vs 0.5) because fruit is
    suggestive, not declarative. Two words in common out of six is
    enough when the user's behaviour already speaks.

    Returns the result string, or None if no matching claim found.
    """
    claims = read_claims(user_id, memory_dir)
    for claim in claims:
        if _similar(claim["fact"], text, threshold=threshold):
            return file_claim(
                user_id, claim["fact"], witness_type, memory_dir,
                abundance=abundance,
            )
    return None
