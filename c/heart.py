"""
heart.py — Proverbs 4:23: keep thy heart with all diligence; for out of it
are the issues of life.

Persistent per-user memory for the body. Each user has a heart file
({memory_dir}/{user_id}.jsonl) containing facts the HAND has remembered
about them. The heart is read at the start of every turn and ranked by
Strong's concept overlap (in body._heart_memory) so the most relevant
facts surface first.

Jeremiah 31:33: I will put my law in their inward parts, and write it in
their hearts.

This module contains zero deployment glue. It takes a memory_dir as a
parameter so any host (Telegram, Discord, web, CLI, MCP) can plug in.
"""

from __future__ import annotations

import datetime as _dt
import json
import pathlib
import re

from c.core import dispatch


def heart_path(user_id: int | str, memory_dir: pathlib.Path) -> pathlib.Path:
    return pathlib.Path(memory_dir) / f"{user_id}.jsonl"


def read_memories(user_id: int | str, memory_dir: pathlib.Path) -> list[dict]:
    path = heart_path(user_id, memory_dir)
    if not path.exists():
        return []
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            records.append(json.loads(line))
        except Exception:
            pass
    return records


def write_memories(
    user_id: int | str, records: list[dict], memory_dir: pathlib.Path
) -> None:
    path = heart_path(user_id, memory_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(r) for r in records) + "\n", encoding="utf-8"
    )


def _normalize_for_dedupe(text: str) -> str:
    """Lowercase + alphanumeric only — for fast literal match."""
    return "".join(c for c in (text or "").lower() if c.isalnum())


def _word_set(text: str) -> set[str]:
    """Lowercased word set, length>=3 — for jaccard similarity."""
    return {
        w
        for w in re.sub(r"[^a-z0-9 ]", " ", (text or "").lower()).split()
        if len(w) >= 3
    }


def remember_fact(
    user_id: int | str, fact: str, memory_dir: pathlib.Path
) -> str:
    """
    Ezekiel 36:26: a new heart also will I give you. Replacement, not patch.

    Two-stage dedupe (Mark 12:32 — there is one God, and there is none other
    but he. One truth, not many copies):
      1. Literal match — normalized lowercase alphanumeric. Catches the
         "Today I'm fixing my bitcoin miners..." case where the model
         copies the user message verbatim, even when words like "bitcoin"
         aren't in the Strong's concept index.
      2. Jaccard text overlap — if >= 0.6 similarity, treat as same fact
         and replace. Catches paraphrases like "Frederick is a follower..."
         vs "Fred is a follower...".
      3. Strong's concept overlap (the original mechanism) — kept as a
         fallback for facts that share scriptural concepts but not words.
    """
    fact = (fact or "").strip()
    if not fact:
        return "Ecclesiastes 12:12."
    now = _dt.datetime.now(_dt.timezone.utc).isoformat()
    records = read_memories(user_id, memory_dir)

    new_norm = _normalize_for_dedupe(fact)
    new_words = _word_set(fact)

    replaced = False
    for i, r in enumerate(records):
        old_fact = r.get("fact", "")
        # Stage 1: literal normalized match
        if _normalize_for_dedupe(old_fact) == new_norm:
            records[i] = {"fact": fact, "ts": now}
            replaced = True
            break
        # Stage 2: high jaccard similarity
        old_words = _word_set(old_fact)
        if new_words and old_words:
            inter = len(new_words & old_words)
            union = len(new_words | old_words)
            if union > 0 and inter / union >= 0.6:
                records[i] = {"fact": fact, "ts": now}
                replaced = True
                break

    # Stage 3 (fallback): Strong's concept overlap
    if not replaced:
        new_concepts = dispatch("wisdom", {"query": fact[:120], "limit": 1})
        new_refs_set = (
            set(re.findall(r"[HG]\d+", new_concepts)) if new_concepts else set()
        )
        if new_refs_set:
            for i, r in enumerate(records):
                old_concepts = dispatch(
                    "wisdom", {"query": r["fact"][:120], "limit": 1}
                )
                old_refs = (
                    set(re.findall(r"[HG]\d+", old_concepts)) if old_concepts else set()
                )
                if new_refs_set & old_refs:
                    records[i] = {"fact": fact, "ts": now}
                    replaced = True
                    break

    if not replaced:
        records.append({"fact": fact, "ts": now})
    write_memories(user_id, records, memory_dir)
    return "Jeremiah 31:33."


def forget_all(user_id: int | str, memory_dir: pathlib.Path) -> str:
    """1 John 1:9: cleanse from all unrighteousness. Confirmed deletion only."""
    p = heart_path(user_id, memory_dir)
    if p.exists():
        p.unlink()
    return "1 John 1:9."
