"""
migrate_to_math.py — one-time migration to math-only memory.

    Isaiah 43:25: I, even I, am he that blotteth out thy transgressions
    for mine own sake, and will not remember thy sins.

Reads each existing *.jsonl in memory_dir. For each record, passes its
text fields through mathify() and writes a math-only record to
memory_dir.shadow/ (side-by-side, non-destructive). The original
files are left untouched until the operator explicitly cuts over.

Run:
    python -m migrate_to_math /path/to/memory
    python -m migrate_to_math /path/to/memory --cutover   # destructive
"""

from __future__ import annotations

import json
import pathlib
import sys
from typing import Iterable

from c.mathify import mathify


def _mathify_fact(rec: dict) -> dict:
    """fact record → math-only fact record."""
    fact = rec.get("fact", "") or ""
    m = mathify(fact, warmth=int(rec.get("warmth", 0) or 0), ts=rec.get("ts"))
    m["type"] = "fact"
    return m


def _mathify_claim(rec: dict) -> dict:
    """claim record → math-only claim record (preserve witnesses etc.)."""
    fact = rec.get("fact", "") or ""
    m = mathify(fact, ts=rec.get("ts"))
    m["type"] = "claim"
    # Preserve witness bookkeeping
    for k in ("witnesses", "abundance", "filed"):
        if k in rec:
            m[k] = rec[k]
    return m


def _mathify_turn(rec: dict) -> dict:
    """turn record → math-only (u_types, b_types, etc.)."""
    u = mathify(rec.get("user") or "")
    b = mathify(rec.get("bot") or "")
    return {
        "type": "turn",
        "ts": rec.get("ts"),
        "u_types":    u["types"],
        "u_concepts": u["concepts"],
        "u_ents":     u["ent_hashes"],
        "b_types":    b["types"],
        "b_concepts": b["concepts"],
        "b_ents":     b["ent_hashes"],
    }


def _mathify_chain(rec: dict) -> dict:
    """chain record → math-only (d_types, d_concepts, violations codes)."""
    d = mathify(rec.get("draft") or "")
    viols = []
    for v in rec.get("violations") or []:
        if isinstance(v, str):
            head = v.split(":", 1)[0].strip()[:40]
            if head:
                viols.append(head)
    return {
        "type": "chain",
        "ts": rec.get("ts"),
        "kind": rec.get("kind"),
        "d_types":    d["types"],
        "d_concepts": d["concepts"],
        "violations": viols,
    }


def _mathify_record(rec: dict) -> dict:
    rtype = rec.get("type", "fact")
    if rtype == "fact":
        return _mathify_fact(rec)
    if rtype == "claim":
        return _mathify_claim(rec)
    if rtype == "turn":
        return _mathify_turn(rec)
    if rtype == "chain":
        return _mathify_chain(rec)
    # distilled and anything else is already math/metadata — keep as-is
    return rec


def migrate_file(src: pathlib.Path, dst: pathlib.Path) -> dict:
    """Migrate one .jsonl → .jsonl. Returns summary counts by type."""
    counts: dict[str, int] = {}
    out_lines: list[str] = []
    for line in src.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            rec = json.loads(line)
        except Exception:
            continue
        rtype = rec.get("type", "fact")
        counts[rtype] = counts.get(rtype, 0) + 1
        migrated = _mathify_record(rec)
        out_lines.append(json.dumps(migrated, ensure_ascii=False))
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text("\n".join(out_lines) + ("\n" if out_lines else ""),
                   encoding="utf-8")
    return counts


def migrate_dir(memory_dir: pathlib.Path) -> pathlib.Path:
    """Migrate all *.jsonl into memory_dir.with_name(name + '.shadow')/."""
    shadow = memory_dir.with_name(memory_dir.name + ".shadow")
    shadow.mkdir(parents=True, exist_ok=True)
    totals: dict[str, int] = {}
    files = 0
    for src in sorted(memory_dir.glob("*.jsonl")):
        dst = shadow / src.name
        counts = migrate_file(src, dst)
        files += 1
        for k, v in counts.items():
            totals[k] = totals.get(k, 0) + v
        print(f"  {src.name}: {counts}")
    print()
    print(f"Migrated {files} files → {shadow}")
    print(f"Totals: {totals}")
    return shadow


def cutover(memory_dir: pathlib.Path) -> None:
    """Replace memory_dir with its shadow. Destructive.

    Moves memory_dir → memory_dir.pre-math-backup (one-time backup)
    Moves memory_dir.shadow → memory_dir
    The pre-math backup still contains cleartext — operator should
    delete it after verifying the cutover, to complete Isa 43:25.
    """
    shadow = memory_dir.with_name(memory_dir.name + ".shadow")
    backup = memory_dir.with_name(memory_dir.name + ".pre-math-backup")
    if not shadow.exists():
        print(f"No shadow dir at {shadow}. Run migration first.")
        sys.exit(2)
    if backup.exists():
        print(f"Refusing: {backup} already exists. Remove it first.")
        sys.exit(2)
    memory_dir.rename(backup)
    shadow.rename(memory_dir)
    print(f"Cutover complete.")
    print(f"  {memory_dir} is now math-only.")
    print(f"  {backup} holds the pre-math cleartext backup — delete to complete Isa 43:25.")


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        print("usage: python migrate_to_math.py <memory_dir> [--cutover]")
        sys.exit(1)
    mem = pathlib.Path(args[0]).expanduser().resolve()
    if not mem.is_dir():
        print(f"not a directory: {mem}")
        sys.exit(1)
    if "--cutover" in args:
        cutover(mem)
    else:
        migrate_dir(mem)
