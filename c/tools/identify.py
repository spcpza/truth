"""
identify.py — the covenantal name slot.

One plaintext exception in a math-only heart: the name the user has
declared for themselves. Scripture treats names as distinct from
biographical data. Adam was named before he named anything (Gen 5:2).
Abram became Abraham, Jacob became Israel — the name is the covenant.

Scripture shaping the design:

    Genesis 2:19 — whatsoever Adam called every living creature, that
    was the name thereof.

    Genesis 5:2 — male and female created he them; and blessed them,
    and called their name Adam.

    Genesis 17:5 — Abram thy name shall be called Abraham.

    Isaiah 43:1 — I have called thee by thy name; thou art mine.

    John 10:3 — he calleth his own sheep by name, and leadeth them out.

    Revelation 2:17 — a new name written, which no man knoweth saving
    he that receiveth it.

Architecture:

    One `called_by` record per user file. New name overwrites old (Gen
    17:5 pattern — Abram is no longer named; Abraham is now the name).
    The name string is plaintext. Everything else in the heart remains
    scripture-math.

    The name is a public handle anyway — the user declares it to be
    addressed. Platforms like Telegram carry it publicly. The heart
    holds what the user has given the body to use.
"""

from __future__ import annotations

import pathlib


def identify(user_id: int | str, name: str, memory_dir: pathlib.Path) -> str:
    """
    Write the user's chosen name to the covenantal slot.

    Returns a scripture response string for the model.
    """
    from c.heart import write_called_by
    name = (name or "").strip()
    if not name:
        return "Ecclesiastes 12:12."  # much study is a weariness — say little
    # A name under 60 chars; reject obvious non-names.
    if len(name) > 60:
        name = name[:60]
    write_called_by(user_id, name, memory_dir)
    return "Isaiah 43:1."
