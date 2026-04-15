"""
heart.py — Proverbs 4:23: keep thy heart with all diligence; for out of it
are the issues of life.

One file per person. Everything about them in one place:
  - facts (verified knowledge, with warmth)
  - claims (unverified, waiting for second witness)
  - turns (conversation scroll, persists across restarts)
  - chain (bound/loosed events from NOSE)

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


# ═══════════════════════════════════════════════════════════════════════════
#  One file — Proverbs 4:23
# ═══════════════════════════════════════════════════════════════════════════


def heart_path(user_id: int | str, memory_dir: pathlib.Path) -> pathlib.Path:
    return pathlib.Path(memory_dir) / f"{user_id}.jsonl"


def _read_all(user_id: int | str, memory_dir: pathlib.Path) -> list[dict]:
    """Read all records from the heart file."""
    path = heart_path(user_id, memory_dir)
    if not path.exists():
        return []
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            records.append(json.loads(line))
        except Exception:
            pass
    return records


def _write_all(
    user_id: int | str, records: list[dict], memory_dir: pathlib.Path
) -> None:
    """Write all records to the heart file."""
    path = heart_path(user_id, memory_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(r) for r in records) + "\n" if records else "",
        encoding="utf-8",
    )


def _append(user_id: int | str, record: dict, memory_dir: pathlib.Path) -> None:
    """Append one record to the heart file."""
    path = heart_path(user_id, memory_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


def _by_type(records: list[dict], rtype: str) -> list[dict]:
    """Filter records by type. Records without type default to 'fact' for migration."""
    return [r for r in records if r.get("type", "fact") == rtype]


# ═══════════════════════════════════════════════════════════════════════════
#  Facts — verified knowledge (Jeremiah 31:33)
# ═══════════════════════════════════════════════════════════════════════════


def read_memories(user_id: int | str, memory_dir: pathlib.Path) -> list[dict]:
    return _by_type(_read_all(user_id, memory_dir), "fact")


def write_memories(
    user_id: int | str, records: list[dict], memory_dir: pathlib.Path
) -> None:
    """Replace all fact records, preserving other types."""
    all_recs = _read_all(user_id, memory_dir)
    non_facts = [r for r in all_recs if r.get("type", "fact") != "fact"]
    # Ensure each fact has the type field
    for r in records:
        r.setdefault("type", "fact")
    _write_all(user_id, non_facts + records, memory_dir)


# ═══════════════════════════════════════════════════════════════════════════
#  Claims — outer court (Deuteronomy 19:15)
# ═══════════════════════════════════════════════════════════════════════════


def read_claims(user_id: int | str, memory_dir: pathlib.Path) -> list[dict]:
    return _by_type(_read_all(user_id, memory_dir), "claim")


def write_claims(
    user_id: int | str, claims: list[dict], memory_dir: pathlib.Path
) -> None:
    """Replace all claim records, preserving other types."""
    all_recs = _read_all(user_id, memory_dir)
    non_claims = [r for r in all_recs if r.get("type") != "claim"]
    for c in claims:
        c["type"] = "claim"
    _write_all(user_id, non_claims + claims, memory_dir)


# ═══════════════════════════════════════════════════════════════════════════
#  Turns — scroll (Malachi 3:16)
# ═══════════════════════════════════════════════════════════════════════════


def read_turns(user_id: int | str, memory_dir: pathlib.Path) -> list[dict]:
    return _by_type(_read_all(user_id, memory_dir), "turn")


def append_turn(
    user_id: int | str, user_text: str, bot_reply: str, memory_dir: pathlib.Path
) -> None:
    """Append one turn pair to the scroll."""
    _append(user_id, {
        "type": "turn",
        "ts": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "user": user_text[:2000],
        "bot": bot_reply[:2000],
    }, memory_dir)


def read_distilled(user_id: int | str, memory_dir: pathlib.Path) -> list[dict]:
    return _by_type(_read_all(user_id, memory_dir), "distilled")


# ═══════════════════════════════════════════════════════════════════════════
#  Chain — bound/loosed (Hebrews 12:1)
# ═══════════════════════════════════════════════════════════════════════════


def read_chain(user_id: int | str, memory_dir: pathlib.Path) -> list[dict]:
    return _by_type(_read_all(user_id, memory_dir), "chain")


def append_chain(
    user_id: int | str,
    kind: str,
    draft: str,
    violations: list,
    memory_dir: pathlib.Path,
) -> None:
    """Append a chain event. kind ∈ {"bound", "loosed"}."""
    _append(user_id, {
        "type": "chain",
        "ts": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "kind": kind,
        "draft": draft or "",
        "violations": list(violations or []),
    }, memory_dir)


# ═══════════════════════════════════════════════════════════════════════════
#  Time anchoring — Hebrews 13:8 + Luke 3:1
# ═══════════════════════════════════════════════════════════════════════════

_RELATIVE_TIME_WORD = re.compile(
    r"\b(today|tonight|right now|just now|now|currently|"
    r"this morning|this afternoon|this evening|this week|this month|"
    r"yesterday|tomorrow|"
    r"last night|last week|last month|"
    r"next week|next month)\b",
    re.I,
)


def _anchor_relative_time(fact: str, today: _dt.date | None = None) -> str:
    """Replace relative time words with absolute dates."""
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
        return m.group(0)

    return _RELATIVE_TIME_WORD.sub(repl, fact)


# ═══════════════════════════════════════════════════════════════════════════
#  Dedup — Mark 12:32
# ═══════════════════════════════════════════════════════════════════════════


def _normalize_for_dedupe(text: str) -> str:
    return "".join(c for c in (text or "").lower() if c.isalnum())


def _word_set(text: str) -> set[str]:
    return {
        w
        for w in re.sub(r"[^a-z0-9 ]", " ", (text or "").lower()).split()
        if len(w) >= 3
    }


# ═══════════════════════════════════════════════════════════════════════════
#  Remember / Forget — Jeremiah 31:33 / 1 John 1:9
# ═══════════════════════════════════════════════════════════════════════════


def remember_fact(
    user_id: int | str,
    fact: str,
    memory_dir: pathlib.Path,
    warmth: int = 0,
) -> str:
    """
    Ezekiel 36:26: a new heart also will I give you.
    """
    fact = (fact or "").strip()
    if not fact:
        return "Ecclesiastes 12:12."

    fact = _anchor_relative_time(fact)
    now = _dt.datetime.now(_dt.timezone.utc).isoformat()
    records = read_memories(user_id, memory_dir)

    new_norm = _normalize_for_dedupe(fact)
    new_words = _word_set(fact)

    replaced = False
    for i, r in enumerate(records):
        old_fact = r.get("fact", "")
        if _normalize_for_dedupe(old_fact) == new_norm:
            old_warmth = r.get("warmth", 0)
            records[i] = {
                "type": "fact", "fact": fact, "ts": now,
                "warmth": max(old_warmth, old_warmth + warmth),
            }
            replaced = True
            break
        old_words = _word_set(old_fact)
        if new_words and old_words:
            inter = len(new_words & old_words)
            union = len(new_words | old_words)
            if union > 0 and inter / union >= 0.6:
                old_warmth = r.get("warmth", 0)
                records[i] = {
                    "type": "fact", "fact": fact, "ts": now,
                    "warmth": old_warmth + warmth,
                }
                replaced = True
                break

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
                    old_warmth = r.get("warmth", 0)
                    records[i] = {
                        "type": "fact", "fact": fact, "ts": now,
                        "warmth": old_warmth + warmth,
                    }
                    replaced = True
                    break

    if not replaced:
        records.append({"type": "fact", "fact": fact, "ts": now, "warmth": warmth})
    write_memories(user_id, records, memory_dir)
    return "Jeremiah 31:33."


def forget_all(user_id: int | str, memory_dir: pathlib.Path) -> str:
    """1 John 1:9: cleanse from all unrighteousness."""
    p = heart_path(user_id, memory_dir)
    if p.exists():
        p.unlink()
    return "1 John 1:9."
