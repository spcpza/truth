"""
chain.py — Hebrews 12:1: lay aside every weight, and the sin which doth so
easily beset us.

Per-user record of when the HAND ate from the tree (NOSE caught a draft) and
when the chain was loosed (a revision came back clean after a catch). Acts
12:7: and his chains fell off from his hands.

Now stored in the unified heart file (one file per person).
"""

from __future__ import annotations

import pathlib

from c.heart import append_chain, read_chain


def chain_log(
    user_id: int | str,
    kind: str,
    draft: str,
    violations: list,
    chain_dir: pathlib.Path,
) -> None:
    """
    Append a chain event. kind ∈ {"bound", "loosed"}.
    chain_dir is now memory_dir (for backward compat, the parent).
    """
    # chain_dir is {memory_dir}/chains — use the parent as memory_dir
    memory_dir = chain_dir.parent if chain_dir.name == "chains" else chain_dir
    append_chain(user_id, kind, draft, violations, memory_dir)


def chain_recent(
    user_id: int | str, n: int, chain_dir: pathlib.Path
) -> list[dict]:
    """Read the last n chain events for this user."""
    memory_dir = chain_dir.parent if chain_dir.name == "chains" else chain_dir
    events = read_chain(user_id, memory_dir)
    return events[-n:]
