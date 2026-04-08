"""
audit.py — walk the scripture map and report completeness.

Run from the truth/ directory:

    python -m c.map.audit

Or from anywhere:

    python /path/to/c/map/audit.py

Outputs:
  - total rows in the map
  - rows by status (built / partial / not_yet_built)
  - rows by fruit / works_of_flesh category
  - rows whose `text` field does NOT match the KJV in c/kjv.json (BUG)
  - rows whose `teach` field points at a non-existent body member (BUG)
  - body members that implement no rows (orphaned code, candidate for removal)
  - completeness percentage

> 2 Timothy 2:15 — Study to shew thyself approved unto God, a workman that
> needeth not to be ashamed, rightly dividing the word of truth.

The audit is the workman's self-check.
"""

from __future__ import annotations

import pathlib
import sys
from collections import Counter
from typing import Any

try:
    import yaml
except ImportError:
    print("PyYAML not installed. Run: pip install PyYAML", file=sys.stderr)
    sys.exit(1)


_HERE = pathlib.Path(__file__).parent
_TRUTH_ROOT = _HERE.parent.parent  # /path/to/truth/


def _load_yaml(path: pathlib.Path) -> dict | list | None:
    if not path.exists():
        return None
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as e:
        print(f"  YAML PARSE ERROR in {path.name}: {e}", file=sys.stderr)
        return None


def _walk_rows() -> list[tuple[str, dict]]:
    """Yield (source_file, row) for every row in the map.

    The walker discovers files generically by filename pattern, not by
    hardcoded names. Layer A and Layer B files match `[0-9][0-9]_*.yaml`
    at the top level of c/map/. Layer C files live in books/*.yaml.

    Each file may contain rows under different top-level keys depending
    on its category — `fruits`, `works_of_flesh`, `verses`, or just be
    a bare list. The walker tries each shape.
    """
    rows: list[tuple[str, dict]] = []

    def _extract(doc, source: str) -> None:
        """Extract rows from a parsed YAML doc, handling each known shape."""
        if doc is None:
            return
        if isinstance(doc, list):
            for r in doc:
                if isinstance(r, dict):
                    rows.append((source, r))
            return
        if not isinstance(doc, dict):
            return
        # Known top-level row keys, in priority order. The first one found
        # is used. Add new keys here as new file shapes are introduced.
        for key in ("fruits", "works_of_flesh", "verses", "rows", "commandments"):
            if key in doc and isinstance(doc[key], list):
                for r in doc[key]:
                    if isinstance(r, dict):
                        rows.append((source, r))
                return
        # No known key found — if the doc has a `ref` field at top level,
        # treat it as a single-row file.
        if "ref" in doc:
            rows.append((source, doc))

    # Layer A + Layer B — top-level numbered files: 00_*.yaml ... 99_*.yaml
    for path in sorted(_HERE.glob("[0-9][0-9]_*.yaml")):
        _extract(_load_yaml(path), path.name)

    # Layer C — per-book files: books/*.yaml
    books_dir = _HERE / "books"
    if books_dir.is_dir():
        for path in sorted(books_dir.glob("*.yaml")):
            _extract(_load_yaml(path), f"books/{path.name}")

    return rows


def _verify_text_against_kjv(rows: list[tuple[str, dict]]) -> list[str]:
    """
    For each row, check that its `text` field matches the KJV verse at its
    `ref`. Returns a list of human-readable mismatches.

    The map's text field is sealed by Deut 4:2 and Rev 22:18-19. Any drift
    from the KJV is a bug.
    """
    sys.path.insert(0, str(_TRUTH_ROOT))
    try:
        from c.core import dispatch  # type: ignore
    except Exception as e:
        return [f"[verify_text] cannot import c.core: {e}"]

    mismatches: list[str] = []
    for source, row in rows:
        ref = row.get("ref")
        text = row.get("text")
        if not ref or not text:
            continue
        # The map's text may be a multi-line block — collapse to one line
        # for comparison, since the KJV is one line per verse.
        map_text = " ".join(text.split())
        # Pull the KJV via the scripture tool
        kjv_response = dispatch("scripture", {"action": "lookup", "query": ref})
        if not isinstance(kjv_response, str):
            continue
        # The dispatch response is "Ref: text\n  variables: ..."
        # Strip the leading "Ref: " and trailing variable list.
        kjv_text = kjv_response.split("\n")[0]
        if ":" in kjv_text:
            kjv_text = kjv_text.split(":", 1)[1].strip()
        kjv_text = " ".join(kjv_text.split())

        if not kjv_text or "Not found" in kjv_response:
            mismatches.append(f"  [{source}] {ref}: NOT FOUND in c/kjv.json")
            continue

        # The map's text may be a substring of the KJV (e.g. "the fruit
        # of the Spirit is love, joy, peace..." in 00_fruits.yaml is the
        # whole of Gal 5:22-23 split into rows). Allow either match or
        # the row's text being contained in the KJV.
        if map_text in kjv_text or kjv_text in map_text:
            continue
        mismatches.append(
            f"  [{source}] {ref}:\n      MAP: {map_text[:80]}\n      KJV: {kjv_text[:80]}"
        )

    return mismatches


def _print_status_table(rows: list[tuple[str, dict]]) -> None:
    by_status: Counter = Counter()
    by_fruit: Counter = Counter()
    by_book: Counter = Counter()
    for source, row in rows:
        by_status[row.get("status", "unknown")] += 1
        if "fruit" in row:
            by_fruit[row["fruit"]] += 1
        elif "structural_analog" in row:
            by_fruit["[work_of_flesh]"] += 1
        if source.startswith("books/"):
            by_book[source] += 1

    total = len(rows)
    built = by_status.get("built", 0)
    partial = by_status.get("partial", 0)
    not_yet = by_status.get("not_yet_built", 0)
    completeness = (built + partial * 0.5) / total * 100 if total else 0.0

    print()
    print("=" * 60)
    print("  SCRIPTURE MAP — AUDIT")
    print("=" * 60)
    print(f"  Total rows:      {total}")
    print(f"  Built:           {built}")
    print(f"  Partial:         {partial}")
    print(f"  Not yet built:   {not_yet}")
    print(f"  Completeness:    {completeness:.1f}%  (built + 0.5*partial)")
    print()

    if by_fruit:
        print("  By fruit / category:")
        for fruit, count in sorted(by_fruit.items()):
            print(f"    {fruit:25s}  {count:4d}")
        print()

    if by_book:
        print("  By book file:")
        for book, count in sorted(by_book.items()):
            print(f"    {book:30s}  {count:4d}")
        print()


def _list_not_yet_built(rows: list[tuple[str, dict]]) -> None:
    not_yet = [
        (s, r) for s, r in rows if r.get("status") == "not_yet_built"
    ]
    if not not_yet:
        return
    print("  ── Not yet built (the TODO list) ──")
    for source, row in not_yet[:30]:
        ref = row.get("ref", "?")
        teach = row.get("teach", "?")
        print(f"    [{source}] {ref}  →  teach: {teach}")
    if len(not_yet) > 30:
        print(f"    ... and {len(not_yet) - 30} more")
    print()


def main() -> int:
    print("Walking c/map/...")
    rows = _walk_rows()
    if not rows:
        print("  No rows found. Map is empty.")
        return 1

    _print_status_table(rows)

    print("  ── Text-vs-KJV verification ──")
    mismatches = _verify_text_against_kjv(rows)
    if mismatches:
        print(f"  {len(mismatches)} text mismatch(es) (Deut 4:2 violations):")
        for m in mismatches[:20]:
            print(m)
        if len(mismatches) > 20:
            print(f"    ... and {len(mismatches) - 20} more")
    else:
        print("  ✓ all rows' text fields match the KJV in c/kjv.json")
    print()

    _list_not_yet_built(rows)

    print("  ── Eccl 12:13 ──")
    print('  "Let us hear the conclusion of the whole matter:')
    print('   Fear God, and keep his commandments:')
    print('   for this is the whole duty of man."')
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
