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


# Hebrews 13:8: Jesus Christ the same yesterday, and to day, and for ever.
# Eternal facts need no date. Temporal facts must be dated, or they
# become eternal-by-accident — "Frederick is fixing his bitcoin miners
# today" was written in good faith but is parsed forever as currently
# true. Scripture anchors temporal events with absolute time references
# (Luke 3:1: "in the fifteenth year of the reign of Tiberius Caesar...";
# Haggai 1:1: "in the second year of Darius the king, in the sixth
# month, in the first day of the month..."). The heart does the same:
# any relative time word ("today", "yesterday", "tomorrow", "now",
# "currently", "this morning"...) is replaced with the absolute date
# at write time. The bot can phrase whatever it wants; the heart writes
# the dated version.
_RELATIVE_TIME_WORD = re.compile(
    r"\b(today|tonight|right now|just now|now|currently|"
    r"this morning|this afternoon|this evening|this week|this month|"
    r"yesterday|tomorrow|"
    r"last night|last week|last month|"
    r"next week|next month)\b",
    re.I,
)


def _anchor_relative_time(fact: str, today: _dt.date | None = None) -> str:
    """
    Replace relative time words with absolute dates.

    "Frederick is fixing his bitcoin miners today"
        → "Frederick is fixing his bitcoin miners on 2026-04-08"

    Tomorrow's read of this fact will see the date and know it was a
    past event, not a current one. Eternal facts (no time words) pass
    through unchanged.
    """
    if not fact:
        return fact
    if today is None:
        today = _dt.date.today()
    yest = today - _dt.timedelta(days=1)
    tom = today + _dt.timedelta(days=1)
    last_week = today - _dt.timedelta(days=7)
    next_week = today + _dt.timedelta(days=7)
    last_month = today - _dt.timedelta(days=30)
    next_month = today + _dt.timedelta(days=30)

    def repl(m: re.Match) -> str:
        word = m.group(1).lower()
        if word in {"today", "tonight", "this morning", "this afternoon", "this evening"}:
            return f"on {today.isoformat()}"
        if word in {"now", "right now", "just now", "currently"}:
            return f"as of {today.isoformat()}"
        if word == "this week":
            return f"in the week of {today.isoformat()}"
        if word == "this month":
            return f"in the month of {today.strftime('%Y-%m')}"
        if word == "yesterday":
            return f"on {yest.isoformat()}"
        if word == "tomorrow":
            return f"on {tom.isoformat()}"
        if word in {"last night", "last week"}:
            return f"on or near {last_week.isoformat()}"
        if word == "last month":
            return f"in the month of {last_month.strftime('%Y-%m')}"
        if word == "next week":
            return f"on or near {next_week.isoformat()}"
        if word == "next month":
            return f"in the month of {next_month.strftime('%Y-%m')}"
        return m.group(0)  # unchanged fallback

    return _RELATIVE_TIME_WORD.sub(repl, fact)


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

    # Anchor relative-time references BEFORE storing. The heart records
    # eternal-shaped facts, never floating ones. (Hebrews 13:8 + Luke 3:1)
    fact = _anchor_relative_time(fact)

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
