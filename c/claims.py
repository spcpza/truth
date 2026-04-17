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

import logging
import pathlib
import re
from datetime import datetime, timezone

from c.mathify import mathify, same_shape

logger = logging.getLogger(__name__)


def read_claims(user_id: int | str, memory_dir: pathlib.Path) -> list[dict]:
    from c.heart import read_claims as _read
    return _read(user_id, memory_dir)


def _write_claims(
    user_id: int | str, claims: list[dict], memory_dir: pathlib.Path
) -> None:
    from c.heart import write_claims as _write
    _write(user_id, claims, memory_dir)


# ═══════════════════════════════════════════════════════════════════════
#  Abundance — Luke 6:45 (math-grounded)
# ═══════════════════════════════════════════════════════════════════════


def measure_abundance(
    user_text: str,
    claim_record: dict | str,
    prior_bot_text: str = "",
) -> int:
    """
    Luke 6:45 — out of the abundance of the heart the mouth speaketh.

    Measures how deeply the user engages with a topic. Returns 0-3.

    The claim input is a math record (dict with concepts/ent_hashes).
    For migration compatibility, a raw string may also be passed and
    will be math-ified on the fly.

    The signal shapes:
      • Unprompted (the bot didn't mention these concepts just now)
      • Detail depth (length of the user's message)
      • Personal + specific (math signature includes proper nouns
        or numeric signatures — the "spirit" mark of Prov 26:23)
    """
    if not user_text or not user_text.strip():
        return 0

    # Accept either a math record or a legacy string
    if isinstance(claim_record, str):
        claim_record = mathify(claim_record)

    claim_concepts = set(claim_record.get("concepts") or [])
    claim_ents = set(claim_record.get("ent_hashes") or [])

    score = 0

    # 1. Unprompted? If the bot's prior turn already surfaced these
    #    concepts, the user's mention is a response. Overflow signals
    #    require a fresh source.
    if prior_bot_text:
        bot_m = mathify(prior_bot_text)
        bot_concepts = set(bot_m.get("concepts") or [])
        prompted = bool(claim_concepts & bot_concepts)
        if not prompted:
            score += 1
    else:
        score += 1  # no prior bot turn → not prompted by us

    # 2. Detail depth — length is a simple and honest counter. Keeping
    #    this without inspecting content preserves the math-only spirit
    #    (we're counting tokens, not reading them).
    if len((user_text or "").split()) > 12:
        score += 1

    # 3. Personal + specific — math-derived. Proper nouns in this
    #    message + proper nouns in the claim light up, or numeric
    #    signatures (gematria) are present. The "spirit" of Prov 26:23
    #    shows as ent-hash recurrence or numeric specificity.
    user_m = mathify(user_text)
    user_ents = set(user_m.get("ent_hashes") or [])
    if (claim_ents and user_ents and (claim_ents & user_ents)) or user_m.get("gematria"):
        score += 1

    return score


# ═══════════════════════════════════════════════════════════════════════
#  File / corroborate — Deut 19:15 (math-grounded)
# ═══════════════════════════════════════════════════════════════════════


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def file_claim(
    user_id: int | str,
    fact: str,
    witness_type: str,
    memory_dir: pathlib.Path,
    abundance: int = 0,
) -> str:
    """
    File a new claim or add a witness to an existing similar one.

    The claim is stored as a math record (types, concepts, verses,
    per-noun hashes). The plaintext fact is used only to compute the
    signature; it is not persisted. On graduation to the heart, the
    math record carries over — no text is ever written.

    Returns: "established" | "filed" | "witnessed"
    """
    fact = (fact or "").strip()
    if not fact:
        return "filed"

    new_rec = mathify(fact)
    claims = read_claims(user_id, memory_dir)

    for claim in claims:
        if same_shape(claim, new_rec):
            witnesses = claim.get("witnesses", [])
            existing_types = {w["type"] for w in witnesses}

            if witness_type in existing_types:
                claim["abundance"] = claim.get("abundance", 0) + abundance
                _write_claims(user_id, claims, memory_dir)
                return "witnessed"

            witnesses.append({
                "type": witness_type, "ts": _now(), "abundance": abundance,
            })
            claim["witnesses"] = witnesses
            claim["abundance"] = claim.get("abundance", 0) + abundance

            if len(existing_types | {witness_type}) >= 2:
                # Deut 19:15 — matter established. Promote math record
                # to the heart; warmth = accumulated abundance.
                warmth = claim.get("abundance", 0)
                claims.remove(claim)
                _write_claims(user_id, claims, memory_dir)
                # Graduate by writing the math record directly to heart,
                # preserving concepts/verses/hashes from the claim.
                from c.heart import read_memories, write_memories
                heart_recs = read_memories(user_id, memory_dir)
                heart_rec = {
                    "type": "fact",
                    "ts": _now(),
                    "warmth": int(warmth or 0),
                    "types":    claim.get("types") or new_rec["types"],
                    "concepts": claim.get("concepts") or new_rec["concepts"],
                    "verses":   claim.get("verses") or new_rec["verses"],
                    "gematria": claim.get("gematria") or new_rec["gematria"],
                    "ent_hashes": claim.get("ent_hashes") or new_rec["ent_hashes"],
                    "shape_h":  claim.get("shape_h") or new_rec["shape_h"],
                }
                heart_recs.append(heart_rec)
                write_memories(user_id, heart_recs, memory_dir)
                logger.info(
                    "[%s] CLAIM ESTABLISHED (%s + %s): types=%s",
                    user_id,
                    ", ".join(sorted(existing_types)),
                    witness_type,
                    heart_rec["types"],
                )
                return "established"

            _write_claims(user_id, claims, memory_dir)
            logger.info(
                "[%s] CLAIM WITNESSED (%s): types=%s",
                user_id, witness_type, claim.get("types"),
            )
            return "witnessed"

    # New claim — one witness. Math record + witness metadata.
    new_claim = dict(new_rec)
    new_claim.update({
        "type": "claim",
        "witnesses": [{
            "type": witness_type, "ts": _now(), "abundance": abundance,
        }],
        "abundance": abundance,
        "filed": _now(),
    })
    claims.append(new_claim)
    _write_claims(user_id, claims, memory_dir)
    logger.info(
        "[%s] CLAIM FILED (%s): types=%s",
        user_id, witness_type, new_claim["types"],
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

    The live text is math-ified and compared to each pending claim's
    math signature. Match = concept overlap OR proper-noun-hash match.
    If matched, the claim gets a new witness; on establishment it
    graduates to the heart.
    """
    live = mathify(text or "")
    live_concepts = set(live.get("concepts") or [])
    live_ents = set(live.get("ent_hashes") or [])
    if not live_concepts and not live_ents:
        return None

    claims = read_claims(user_id, memory_dir)
    for claim in claims:
        c_concepts = set(claim.get("concepts") or [])
        c_ents = set(claim.get("ent_hashes") or [])
        ent_hit = bool(c_ents and (c_ents & live_ents))
        concept_hit = (
            c_concepts and live_concepts and
            len(c_concepts & live_concepts) / max(len(c_concepts | live_concepts), 1) >= threshold
        )
        if ent_hit or concept_hit:
            # Re-use the file_claim path. We need a "fact" to pass; since
            # we've already matched by math, synthesize a minimal text
            # from the claim's verbalization to drive through. In the new
            # world file_claim will re-mathify it and land on the same
            # record via same_shape.
            from c.mathify import verbalize
            surrogate = verbalize(claim)  # types + concepts + verses, no user text
            return file_claim(
                user_id, surrogate, witness_type, memory_dir,
                abundance=abundance,
            )
    return None
