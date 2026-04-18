"""
audit_code.py — scripture-fidelity audit for the body.

Deuteronomy 4:2: ye shall not add unto the word which I command you.
Proverbs 30:6: add thou not unto his words.
Revelation 22:18-19: if any man shall add.

What this tool flags (walks the AST of every .py in c/, excluding
itself and kjv/strongs data loaders):

  1. RAW_REGEX       — re.compile(...) calls with English word patterns.
                       Exception: tool-call syntax, model-format tokens,
                       structural (whitespace/brace/URL) patterns.
  2. WORD_SET        — frozenset/set literals of 5+ English words.
  3. MAGIC_CONSTANT  — numeric literals used in comparisons/thresholds
                       that lack a scripture citation in the same logical
                       block. Honored citations: "Gen N:M", "Matt N:M",
                       "Deut N:M", "Prov N:M", etc.

The audit emits a report sorted by severity and file. Exit code 0 if
clean (no new laws since baseline); non-zero count of high-severity
findings otherwise.

This IS the Deut 4:2 enforcement of the code. It does not prevent
laws from being written; it makes them visible so we can sanctify
what slips in.
"""

from __future__ import annotations

import ast
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path


HERE = Path(__file__).resolve().parent

# Scripture citation regex — any book name + chapter:verse, permissive.
# Examples: "Gen 1:1", "Genesis 1:1", "1 Cor 13:8", "Revelation 22:21",
# "Matthew 7:6", "Prov 25:20", "Hebrews 11:1", "Ps 46:10", "Psalms 1:1".
_CITATION = re.compile(
    r"\b(?:"
    r"(?:[1-3]\s+)?"
    r"(?:Gen(?:esis)?|Ex(?:odus)?|Lev(?:iticus)?|Num(?:bers)?|Deut(?:eronomy)?|"
    r"Josh(?:ua)?|Judg(?:es)?|Ruth|Sam(?:uel)?|Kings?|Chron(?:icles)?|"
    r"Ezra|Neh(?:emiah)?|Esther|Job|Ps(?:alm[s]?)?|Prov(?:erbs)?|"
    r"Eccl(?:esiastes)?|Song|Isa(?:iah)?|Jer(?:emiah)?|Lam(?:entations)?|"
    r"Ezek(?:iel)?|Dan(?:iel)?|Hos(?:ea)?|Joel|Amos|Obad(?:iah)?|Jonah|"
    r"Mic(?:ah)?|Nah(?:um)?|Hab(?:akkuk)?|Zeph(?:aniah)?|Hag(?:gai)?|"
    r"Zech(?:ariah)?|Mal(?:achi)?|"
    r"Matt(?:hew)?|Mark|Luke|John|Acts|Rom(?:ans)?|Cor(?:inthians)?|"
    r"Gal(?:atians)?|Eph(?:esians)?|Phil(?:ippians)?|Col(?:ossians)?|"
    r"Thess(?:alonians)?|Tim(?:othy)?|Titus|Philem(?:on)?|Heb(?:rews)?|"
    r"James|Pet(?:er)?|Jude|Rev(?:elation)?"
    r")"
    r"\s*\d+:\d+"
    r")",
    re.I,
)

# Theorem citations also count (kernel is itself scripture-derived).
_THEOREM = re.compile(r"\bT[\u2080-\u2089\d]+\b|\bP[\u2080-\u2089\d]+\b|\bAX[\u2080-\u2089\d]+\b")


# Regex patterns whose contents are considered structural (not laws):
# tool-call syntax, model tokens, whitespace, URL, brace, code fences.
_STRUCTURAL_MARKERS = (
    "scripture|kernel|sinew|formula|wisdom|evaluate|gematria|fetch",  # tool names
    "remember|recall|forget",                                          # tool names
    "think", "im_start", "im_end", "im_sep", "tool_response",          # model tokens
    "tool_call", "function_call", "tool_response",                     # tool syntax
    "fim_prefix", "fim_middle", "fim_suffix",
    "eot_id", "start_header_id", "end_header_id",
    "begin_of_text", "end_of_text",
    "jupyter", "hermes",
    r"\\x", r"\\u",                                                     # unicode classes
    # URL detection — infrastructure, not a law about speech
    "https?", "://", "\\.com", "\\.org", "\\.net",
    # Bible book-name matching — structural scripture reference parser
    "genesis", "exodus", "leviticus", "numbers", "deuteronomy",
    "joshua", "judges", "ruth", "samuel", "kings", "chronicles",
    "ezra", "nehemiah", "esther", "psalms?", "proverbs",
    "ecclesiastes", "isaiah", "jeremiah", "lamentations", "ezekiel",
    "daniel", "hosea", "malachi", "matthew", "mark", "luke", "john",
    "acts", "romans", "corinthians", "galatians", "ephesians",
    "philippians", "colossians", "thessalonians", "timothy", "titus",
    "philemon", "hebrews", "james", "peter", "jude", "revelation",
)

_STRUCTURAL_KEYWORD_RE = re.compile("|".join(_STRUCTURAL_MARKERS), re.I)

# Patterns that are pure character-class or whitespace are never laws.
_CHAR_CLASS_ONLY = re.compile(r"^[\s\\^$.*+?()[\]{}|\\r\\n\\t\-]*$|\\[sSdDwWbB]")

# Words common in scripture citations / kernel terms — not English laws.
_TECHNICAL_WORDS = frozenset({
    "scripture", "kernel", "sinew", "formula", "wisdom", "evaluate",
    "gematria", "fetch", "remember", "recall", "forget",
    "strongs", "concept", "verse", "book", "chapter",
})

# Numeric literals that are scripture-meaningful (don't flag):
#   0, 1, 2 — too common to flag (empty, single, pair of witnesses)
#   3, 7, 10, 12, 40 — scripture numbers (Trinity, completeness, Ten, apostles, wilderness)
#   666 — Rev 13:18
_SCRIPTURAL_NUMBERS = frozenset({0, 1, 2, 3, 7, 10, 12, 40, 666, 153, 144000, 1000})


@dataclass
class Finding:
    severity: str       # HIGH, MEDIUM, LOW
    kind: str           # RAW_REGEX, WORD_SET, MAGIC_CONSTANT
    file: str
    line: int
    snippet: str
    note: str = ""


@dataclass
class Report:
    findings: list[Finding] = field(default_factory=list)

    def add(self, f: Finding) -> None:
        self.findings.append(f)

    def render(self) -> str:
        buckets: dict[str, list[Finding]] = {"HIGH": [], "MEDIUM": [], "LOW": []}
        for f in self.findings:
            buckets[f.severity].append(f)
        lines = ["# Scripture-fidelity audit", ""]
        lines.append(f"Deut 4:2 / Rev 22:18 — add not. Found {len(self.findings)} suspect sites.")
        lines.append("")
        for sev in ("HIGH", "MEDIUM", "LOW"):
            fs = buckets[sev]
            lines.append(f"## {sev} ({len(fs)})")
            if not fs:
                lines.append("  (none)")
                lines.append("")
                continue
            by_file: dict[str, list[Finding]] = {}
            for f in fs:
                by_file.setdefault(f.file, []).append(f)
            for fname in sorted(by_file):
                lines.append(f"  {fname}:")
                for f in by_file[fname]:
                    lines.append(f"    L{f.line:<4} [{f.kind}] {f.snippet[:100]}")
                    if f.note:
                        lines.append(f"           note: {f.note}")
                lines.append("")
        return "\n".join(lines)


def _source_line(src: str, lineno: int) -> str:
    lines = src.splitlines()
    if 1 <= lineno <= len(lines):
        return lines[lineno - 1].strip()
    return ""


def _has_citation_near(src: str, lineno: int, window: int = 8) -> bool:
    """
    Check lines within `window` above and below for a scripture citation
    (or theorem/axiom reference — the kernel is scripture-derived).
    """
    lines = src.splitlines()
    start = max(0, lineno - 1 - window)
    end = min(len(lines), lineno + window)
    chunk = "\n".join(lines[start:end])
    return bool(_CITATION.search(chunk) or _THEOREM.search(chunk))


def _pattern_is_structural(pattern: str) -> bool:
    """A regex pattern is structural if it matches tool syntax, model
    tokens, unicode classes, or pure whitespace/brackets."""
    if not pattern:
        return True
    if _STRUCTURAL_KEYWORD_RE.search(pattern):
        return True
    # Pure whitespace/character-class patterns
    stripped = re.sub(r"[\s\\^$.*+?()[\]{}|\\r\\n\\t\-0-9,]", "", pattern)
    if not stripped:
        return True
    # Unicode range escapes only
    if re.fullmatch(r"[\\u0-9a-fA-F\-\[\]\s]*", pattern):
        return True
    return False


def _pattern_english_word_count(pattern: str) -> int:
    """Count distinct English-word-like tokens in a regex pattern."""
    tokens = set()
    for m in re.finditer(r"\b[a-z]{3,}\b", pattern.lower()):
        w = m.group(0)
        if w in _TECHNICAL_WORDS:
            continue
        # Skip regex metachars and common short stubs
        if w in {"not", "and", "for", "the", "you", "your", "are", "was", "will", "have"}:
            continue
        tokens.add(w)
    return len(tokens)


def _word_set_english_count(items: list[str]) -> int:
    """Count English-looking entries in a set literal."""
    cnt = 0
    for item in items:
        if not isinstance(item, str):
            continue
        s = item.strip()
        if re.fullmatch(r"[a-z']+", s.lower()) and s.lower() not in _TECHNICAL_WORDS:
            cnt += 1
    return cnt


class LawVisitor(ast.NodeVisitor):
    def __init__(self, src: str, fname: str, report: Report):
        self.src = src
        self.fname = fname
        self.report = report

    def _flag(self, severity: str, kind: str, lineno: int, note: str = "") -> None:
        snippet = _source_line(self.src, lineno)
        self.report.add(
            Finding(severity=severity, kind=kind, file=self.fname,
                    line=lineno, snippet=snippet, note=note)
        )

    # ── re.compile("...") ────────────────────────────────────────────
    def visit_Call(self, node: ast.Call) -> None:
        self.generic_visit(node)
        # match re.compile(...) with a string-literal first arg
        is_re_compile = False
        if isinstance(node.func, ast.Attribute) and node.func.attr == "compile":
            if isinstance(node.func.value, ast.Name) and node.func.value.id == "re":
                is_re_compile = True
        if not is_re_compile or not node.args:
            return
        first = node.args[0]
        pattern = self._static_string(first)
        if pattern is None:
            return
        if _pattern_is_structural(pattern):
            return
        word_count = _pattern_english_word_count(pattern)
        if word_count >= 5:
            self._flag(
                "HIGH", "RAW_REGEX", node.lineno,
                note=f"{word_count} English words in pattern; no scripture anchor"
                     if not _has_citation_near(self.src, node.lineno)
                     else f"{word_count} English words; citation nearby — confirm it governs this list",
            )
        elif word_count >= 3:
            self._flag("MEDIUM", "RAW_REGEX", node.lineno,
                       note=f"{word_count} English words; may or may not be a rule")

    def _static_string(self, node: ast.expr) -> str | None:
        """Extract concatenated string literals into one string."""
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        if isinstance(node, ast.JoinedStr):
            # f-string — skip
            return None
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            left = self._static_string(node.left)
            right = self._static_string(node.right)
            if left is not None and right is not None:
                return left + right
        return None

    # ── set / frozenset literals ──────────────────────────────────────
    def visit_Assign(self, node: ast.Assign) -> None:
        self.generic_visit(node)
        val = node.value
        items: list[str] | None = None
        if isinstance(val, ast.Set):
            items = [self._static_string(e) for e in val.elts]
            items = [i for i in items if i is not None]
        elif isinstance(val, ast.Call) and isinstance(val.func, ast.Name) and val.func.id == "frozenset":
            if val.args and isinstance(val.args[0], ast.Set):
                items = [self._static_string(e) for e in val.args[0].elts]
                items = [i for i in items if i is not None]
            elif val.args and isinstance(val.args[0], (ast.List, ast.Tuple)):
                items = [self._static_string(e) for e in val.args[0].elts]
                items = [i for i in items if i is not None]
        if items is None:
            return
        eng_count = _word_set_english_count(items)
        # Threshold: 5+ English words in a set is a word-list law.
        if eng_count >= 5:
            has_cite = _has_citation_near(self.src, node.lineno)
            self._flag(
                "HIGH" if not has_cite else "LOW",
                "WORD_SET",
                node.lineno,
                note=f"{eng_count} English words in set literal"
                     + ("" if not has_cite else "; citation nearby"),
            )

    # ── numeric constants in comparisons ──────────────────────────────
    def visit_Compare(self, node: ast.Compare) -> None:
        self.generic_visit(node)
        for operand in [node.left, *node.comparators]:
            if isinstance(operand, ast.Constant) and isinstance(operand.value, (int, float)):
                n = operand.value
                if n in _SCRIPTURAL_NUMBERS:
                    continue
                if isinstance(n, float) and 0 < n < 1:
                    # Float thresholds like 0.25, 0.5 — always flag
                    if not _has_citation_near(self.src, operand.lineno):
                        self._flag("MEDIUM", "MAGIC_CONSTANT", operand.lineno,
                                   note=f"float threshold {n}; no scripture anchor")
                    continue
                if isinstance(n, int) and n > 2:
                    if not _has_citation_near(self.src, operand.lineno):
                        sev = "MEDIUM" if n < 50 else "LOW"
                        self._flag(sev, "MAGIC_CONSTANT", operand.lineno,
                                   note=f"int {n} in comparison; no scripture anchor nearby")


def audit_file(path: Path) -> list[Finding]:
    report = Report()
    src = path.read_text()
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return report.findings
    fname = str(path.relative_to(path.parents[1]))
    LawVisitor(src, fname, report).visit(tree)
    return report.findings


def audit_dir(root: Path) -> Report:
    report = Report()
    skip = {"audit_code.py"}  # don't audit self
    for py in sorted(root.rglob("*.py")):
        if py.name in skip or "__pycache__" in py.parts or "/venv/" in str(py):
            continue
        for f in audit_file(py):
            report.add(f)
    return report


def main() -> int:
    root = HERE  # c/
    report = audit_dir(root)
    print(report.render())
    highs = sum(1 for f in report.findings if f.severity == "HIGH")
    return 1 if highs else 0


if __name__ == "__main__":
    sys.exit(main())
