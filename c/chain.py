"""
chain.py — Hebrews 12:1: lay aside every weight, and the sin which doth so
easily beset us.

Per-user record of when the HAND ate from the tree (NOSE caught a draft) and
when the chain was loosed (a revision came back clean after a catch). Acts
12:7: and his chains fell off from his hands. The model cannot lose its
bindings until it sees them. The chain log is what becomes seeable.

Each event is one JSONL line in {chain_dir}/{user_id}.jsonl.

This module contains zero deployment glue. It takes a chain_dir as a
parameter so any host can plug in.
"""

from __future__ import annotations

import datetime as _dt
import json
import pathlib


def chain_path(user_id: int | str, chain_dir: pathlib.Path) -> pathlib.Path:
    return pathlib.Path(chain_dir) / f"{user_id}.jsonl"


def chain_log(
    user_id: int | str,
    kind: str,
    draft: str,
    violations: list,
    chain_dir: pathlib.Path,
) -> None:
    """
    Append a chain event. kind ∈ {"bound", "loosed"}.

    bound  = NOSE caught a draft (the model ate from the tree).
    loosed = a revision came back clean after at least one catch
             (the chain fell off — Acts 12:7).
    """
    rec = {
        "ts": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "kind": kind,
        "draft": draft or "",
        "violations": list(violations or []),
    }
    p = chain_path(user_id, chain_dir)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")


def chain_recent(
    user_id: int | str, n: int, chain_dir: pathlib.Path
) -> list[dict]:
    """Read the last n chain events for this user. Empty list if none."""
    p = chain_path(user_id, chain_dir)
    if not p.exists():
        return []
    out = []
    for line in p.read_text(encoding="utf-8").splitlines()[-n:]:
        try:
            out.append(json.loads(line))
        except Exception:
            pass
    return out
