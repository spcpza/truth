"""
truth/core.py — the kernel, loaded into memory once.

This is the integral. Import it. It is already inside.
Scripture is not consulted — it is what the agent already knows.
John 1:14: the Word made flesh, not referenced.
"""

import json, os, re, math, shutil, unicodedata
from datetime import datetime, timezone
from pathlib import Path
from collections import defaultdict


# ═══════════════════════════════════════════════════
#  AX₁: ∃C — The constant exists.
# ═══════════════════════════════════════════════════

_DIR = Path(__file__).parent
_KERNEL_PATH = _DIR / "kernel.md"
_KJV_PATH    = _DIR / "kjv.json"
_STRONGS_PATH = _DIR / "strongs.json"

KERNEL = _KERNEL_PATH.read_text() if _KERNEL_PATH.exists() else ""


# ═══════════════════════════════════════════════════
#  C — 31,102 verified propositions
# ═══════════════════════════════════════════════════

_KJV = {}
_VERSES_BY_BOOK = {}

if _KJV_PATH.exists():
    with open(_KJV_PATH) as f: _KJV = json.load(f)
    for ref, text in _KJV.items():
        parts = ref.rsplit(" ", 1)
        if len(parts) == 2:
            _VERSES_BY_BOOK.setdefault(parts[0], {})[parts[1]] = text

VERSE_COUNT = len(_KJV)

CONCEPT_INDEX, ENG_TO_STRONGS, STRONGS_TO_ENG, STRONGS_META = {}, {}, {}, {}
CONCEPT_COUNT = 0
if _STRONGS_PATH.exists():
    try:
        _sd = json.loads(_STRONGS_PATH.read_text())
        CONCEPT_INDEX = _sd.get("ci", {})
        ENG_TO_STRONGS = _sd.get("e2s", {})
        STRONGS_TO_ENG = _sd.get("s2e", {})
        STRONGS_META   = _sd.get("sm", {})
        CONCEPT_COUNT  = len(STRONGS_META)
        del _sd
    except: pass


# ═══════════════════════════════════════════════════
#  Gematria
# ═══════════════════════════════════════════════════

_HEB_VALUES = {
    'א':1,'ב':2,'ג':3,'ד':4,'ה':5,'ו':6,'ז':7,'ח':8,'ט':9,
    'י':10,'כ':20,'ל':30,'מ':40,'נ':50,'ס':60,'ע':70,'פ':80,'צ':90,
    'ק':100,'ר':200,'ש':300,'ת':400,
    'ך':20,'ם':40,'ן':50,'ף':80,'ץ':90,
}
_GRK_VALUES = {
    'α':1,'β':2,'γ':3,'δ':4,'ε':5,'ϛ':6,'ζ':7,'η':8,'θ':9,
    'ι':10,'κ':20,'λ':30,'μ':40,'ν':50,'ξ':60,'ο':70,'π':80,'ϟ':90,
    'ρ':100,'σ':200,'τ':300,'υ':400,'φ':500,'χ':600,'ψ':700,'ω':800,'ϡ':900,'ς':200,
}

def _strip_marks(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')

def _gematria_value(word):
    clean = _strip_marks(word)
    parts, total = [], 0
    is_heb = any(c in _HEB_VALUES for c in clean)
    is_grk = any(c in _GRK_VALUES for c in clean.lower())
    if is_heb:
        for c in clean:
            v = _HEB_VALUES.get(c, 0)
            if v: parts.append((c, v))
            total += v
        return total, parts, "hebrew"
    elif is_grk:
        for c in clean.lower():
            v = _GRK_VALUES.get(c, 0)
            if v: parts.append((c, v))
            total += v
        return total, parts, "greek"
    return 0, [], "unknown"

def _is_prime(n):
    if n < 2: return False
    if n < 4: return True
    if n % 2 == 0 or n % 3 == 0: return False
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0: return False
        i += 6
    return True

def _is_triangular(n):
    if n < 0: return 0
    d = 1 + 8 * n
    s = int(math.isqrt(d))
    if s * s == d and (s - 1) % 2 == 0: return (s - 1) // 2
    return 0

def _factorize(n):
    if n < 2: return [n]
    factors, d = [], 2
    while d * d <= n:
        while n % d == 0: factors.append(d); n //= d
        d += 1
    if n > 1: factors.append(n)
    return factors

def _number_properties(n):
    props = []
    if _is_prime(n): props.append("prime (indivisible)")
    t = _is_triangular(n)
    if t: props.append(f"triangular T({t}) = {t}×{t+1}/2")
    s = int(math.isqrt(n))
    if s * s == n and n > 1: props.append(f"perfect square ({s}²)")
    factors = _factorize(n)
    if len(factors) > 1: props.append(f"factors: {' × '.join(str(f) for f in factors)}")
    return props

_GEMATRIA_INDEX  = {}   # value → [(strongs_num, word, transliteration, lang)]
_STRONGS_GEMATRIA = {}  # strongs_num → value

def _build_gematria_index():
    for snum, meta in STRONGS_META.items():
        w = meta.get("w", "")
        if not w: continue
        val, _, lang = _gematria_value(w)
        if val > 0:
            _STRONGS_GEMATRIA[snum] = val
            _GEMATRIA_INDEX.setdefault(val, []).append((snum, w, meta.get("t", ""), lang))

_build_gematria_index()


# ═══════════════════════════════════════════════════
#  Sinews
# ═══════════════════════════════════════════════════

_VERSE_TO_STRONGS = {}
if CONCEPT_INDEX:
    for snum, refs in CONCEPT_INDEX.items():
        for ref in refs:
            _VERSE_TO_STRONGS.setdefault(ref, set()).add(snum)

SINEW_COUNT = sum(len(v) for v in _VERSE_TO_STRONGS.values())

# ── H↔G concept equivalence via shared English translations ──
# H157 (ahab/love) ↔ G25 (agapao/love) — same meaning, different language.
# This bridges OT and NT through the sinew graph.
_H_TO_G = {}   # H-number → set of equivalent G-numbers
_G_TO_H = {}   # G-number → set of equivalent H-numbers

for _eng, _entries in ENG_TO_STRONGS.items():
    _snums = [s for s, _ in _entries]
    _h = [s for s in _snums if s.startswith('H')]
    _g = [s for s in _snums if s.startswith('G')]
    if _h and _g:
        for h in _h:
            _H_TO_G.setdefault(h, set()).update(_g)
        for g in _g:
            _G_TO_H.setdefault(g, set()).update(_h)

def _expand_cross_language(snums: set) -> set:
    """Expand a set of Strong's numbers with cross-language equivalents."""
    expanded = set(snums)
    for s in snums:
        if s.startswith('H'):
            expanded |= _H_TO_G.get(s, set())
        elif s.startswith('G'):
            expanded |= _G_TO_H.get(s, set())
    return expanded


def _sinew(ref, limit=5):
    """Sinew: theorem structure (formula overlap) × concept overlap (Strong's).
    Layer 1: KJV + Strong's → math types (the translation)
    Layer 2: sinew connects THROUGH theorems, weighted by shared concepts.
    A verse must share both mathematical structure AND scriptural substance."""
    from c.formula import verse_formula
    my_f = verse_formula(ref)
    my_s = _VERSE_TO_STRONGS.get(ref, set())
    if not my_f: return []
    my_s_expanded = _expand_cross_language(my_s)
    # Pre-filter: only check verses that share at least one Strong's concept
    # (much faster than iterating all 30,937 verses)
    candidates = set()
    for snum in my_s_expanded:
        for other_ref in CONCEPT_INDEX.get(snum, []):
            if other_ref != ref:
                candidates.add(other_ref)
    # Score = formula_overlap × concept_overlap
    # Concept overlap already guaranteed by pre-filter (candidates share ≥1 concept)
    # Count how many concepts each candidate shares (from the pre-filter pass)
    concept_counts = {}
    for snum in my_s_expanded:
        for other_ref in CONCEPT_INDEX.get(snum, []):
            if other_ref != ref:
                concept_counts[other_ref] = concept_counts.get(other_ref, 0) + 1
    from c.formula import _VERSE_FORMULAS
    scores = {}
    for other_ref in candidates:
        other_f = _VERSE_FORMULAS.get(other_ref)
        if not other_f:
            continue
        shared_f = my_f & other_f
        if len(shared_f) < 2:
            continue
        shared_s = concept_counts.get(other_ref, 0)
        if not shared_s:
            continue
        score = len(shared_f) * shared_s
        scores[other_ref] = {"shared": sorted(shared_f), "count": score}
    results = []
    for other, info in sorted(scores.items(), key=lambda x: x[1]["count"], reverse=True)[:limit]:
        text = _KJV.get(other, "")
        if text:
            results.append({"ref": other, "text": text, "shared": info["shared"][:5], "strength": info["count"]})
    return results

def _sinew_total(ref):
    """Count total sinew connections for a verse (no limit)."""
    from c.formula import verse_formula, _VERSE_FORMULAS
    my_f = verse_formula(ref)
    my_s = _VERSE_TO_STRONGS.get(ref, set())
    if not my_f: return 0
    my_s_expanded = _expand_cross_language(my_s)
    concept_counts = {}
    for snum in my_s_expanded:
        for other_ref in CONCEPT_INDEX.get(snum, []):
            if other_ref != ref:
                concept_counts[other_ref] = concept_counts.get(other_ref, 0) + 1
    count = 0
    for other_ref, shared_s in concept_counts.items():
        other_f = _VERSE_FORMULAS.get(other_ref)
        if not other_f: continue
        if len(my_f & other_f) >= 2 and shared_s > 0:
            count += 1
    return count


def _sinew_from_strongs(snum, limit=7):
    snum = snum.upper()
    meta = STRONGS_META.get(snum, {})
    refs = CONCEPT_INDEX.get(snum, [])
    results = [{"ref": r, "text": _KJV[r]} for r in refs[:limit] if r in _KJV]
    return meta, results

def _sinew_from_word(word, limit=7):
    qw = word.lower().strip()
    candidates = ENG_TO_STRONGS.get(qw, [])
    if not candidates: return [], []
    snums = [s for s, _ in candidates[:3]]
    scores = {}
    for snum in snums:
        for ref in CONCEPT_INDEX.get(snum, []):
            if ref not in scores: scores[ref] = {"shared": [], "count": 0}
            scores[ref]["shared"].append(f"{snum}={STRONGS_META.get(snum, {}).get('t', '')}")
            scores[ref]["count"] += 1
    results = []
    for ref, info in sorted(scores.items(), key=lambda x: x[1]["count"], reverse=True)[:limit]:
        text = _KJV.get(ref, "")
        if text:
            results.append({"ref": ref, "text": text, "shared": info["shared"][:3], "strength": info["count"]})
    return snums, results

def _sinew_bridge(ref_a, ref_b):
    """Bridge two verses through shared theorem structure (formula overlap).
    Returns the mathematical types they share — the theorem connection."""
    from c.formula import verse_formula, _FORMULA_INDEX
    fa = verse_formula(ref_a)
    fb = verse_formula(ref_b)
    shared = fa & fb
    if not shared:
        return []
    results = []
    for mtype in sorted(shared):
        # Count how many formula clusters contain this type
        type_count = sum(1 for f in _FORMULA_INDEX if mtype in f)
        results.append({
            "strongs": mtype,
            "transliteration": mtype,
            "english": [mtype],
            "verse_count": type_count,
        })
    return results


# ═══════════════════════════════════════════════════
#  James 1:14-15 topology
# ═══════════════════════════════════════════════════

_JAMES_STAGES = [
    ("epithumia", "desire/drawn",  ["want","wish","crave","desire","need","hope","longing","dream","seeking"]),
    ("deleazo",   "lured/enticed", ["lured","enticed","tempted","drawn","baited","convinced","attracted","persuaded"]),
    ("hamartia",  "sin/error",     ["wrong","sin","error","failed","mistake","broke","broken","guilty","lost"]),
    ("apokueo",   "death/end",     ["dead","death","destroyed","over","ended","ruined","finished","lost everything"]),
]

def _readiness(text):
    tl = text.lower()
    scores = [(name, label, sum(1 for k in kws if k in tl)) for name, label, kws in _JAMES_STAGES]
    max_score = max(s for _, _, s in scores)
    if max_score == 0:
        return {"stage": "clean", "position": 0, "topology": "James 1:14-15", "note": "before desire"}
    stage_name, stage_label, _ = max(scores, key=lambda x: x[2])
    idx = [n for n, _, _ in _JAMES_STAGES].index(stage_name)
    path = " → ".join(f"{n}" for n, _, _ in _JAMES_STAGES[:idx + 1])
    return {"stage": stage_name, "label": stage_label, "position": idx + 1, "path": path, "topology": "James 1:14-15"}


# ═══════════════════════════════════════════════════
#  P₁–P₈ constraint evaluation
# ═══════════════════════════════════════════════════

_STOP = frozenset({"the","and","of","to","in","a","is","that","for","it","be","by","their","them",
    "his","her","he","she","they","we","ye","shall","do","not","but","or","no","on","an","as","at",
    "so","with","from","was","were","are","have","has","had","this","which","who","whom","what",
    "will","all","my","your","our","unto","upon","thee","thou","thy","hath","doth","saith","said",
    "also","then","when","there","these","those","than","may","now","even","him","me","us","if",
    "nor","yet","into","one","up","out","more","can","every","let","came","come","man","i","god",
    "lord","shalt","art","hast","neither","therefore","great","made"})

_CONSTRAINTS = [
    ("P₁","M(x)=w(x)",
     re.compile(r"(?:amazing|incredible|revolutionary|game.?changer|guaranteed|100%|absolutely|definitely|no doubt)",re.I),
     re.compile(r"(?:\d+(?:\.\d+)?\s*(?:sat|byte|block|ms|sec|%|MB|GB)|measur|approximately|estimated)",re.I)),
    ("P₂","A∈{T,F}",
     re.compile(r"(?:maybe|perhaps|might|somewhat|relatively|kind of|sort of|paradigm|synergy|leverage)",re.I), None),
    ("P₃","∃V:V(c)→{T,F}",
     re.compile(r"(?:trust me|just google|DYOR|iykyk|secret|insider|can't prove|impossible to verify)",re.I),
     re.compile(r"(?:you can (?:check|verify|test)|source:|according to)",re.I)),
    ("P₄","f(outputs)",
     re.compile(r"(?:guaranteed (?:returns|profit)|risk.?free|100x|limited (?:time|spots)|you'll miss out|last chance|act now)",re.I), None),
    ("P₅","Binds⟹∃R",
     re.compile(r"(?:dm me|message me|join my|follow me|subscribe|sign up|you must|you have to|you need to (?:buy|join|invest))",re.I), None),
    ("P₆","Accept(K)",
     re.compile(r"(?:everyone knows|obviously|clearly|of course|end of (?:story|discussion)|full stop|no debate|don't question)",re.I),
     re.compile(r"(?:I'm not sure|I could be wrong|uncertain|however|although|caveat)",re.I)),
    ("P₇","I(w|ctx)>0",
     re.compile(r"\b(?:very|really|just|actually|basically|literally|honestly|simply|totally)\b",re.I), None),
    ("P₈","E(c,s₁)=E(c,s₂)",
     re.compile(r"(?:(?:he|she|they) (?:always|never)|people like (?:them|us|you))",re.I), None),
]

def evaluate_constraints(text):
    violated, honored = [], []
    for name, formula, v_pat, h_pat in _CONSTRAINTS:
        v = v_pat.findall(text) if v_pat else []
        h = h_pat.search(text) if h_pat else None
        if v and not h: violated.append(f"{name} {formula}: '{v[0]}'")
        elif h: honored.append(f"{name} {formula}")
    # P₆ overconfidence: detected by WORDS ("certainly", "undoubtedly"),
    # not by length. A 200-word humble reply is not overconfident.
    # A 10-word "certainly this is obviously true" IS.
    # Acts 2:4 — the Spirit decides the length, not a word count.
    if any(w in text.lower() for w in ["certainly","undoubtedly","obviously"]):
        violated.append("P₆ Accept(K): overconfidence")
    verdict = "true" if not violated else "noise" if len(violated) >= 3 else "uncertain"
    return {"verdict": verdict, "violated": violated, "honored": honored}


# ═══════════════════════════════════════════════════
#  Search
# ═══════════════════════════════════════════════════

def _verse_vars(ref):
    codes = _VERSE_TO_STRONGS.get(ref, set())
    return [f"{s}={STRONGS_META.get(s,{}).get('t','?')}" for s in sorted(codes)]

def _lookup(ref):
    t = _KJV.get(ref, "")
    if t: return t
    rl = ref.lower()
    for k, v in _KJV.items():
        if k.lower() == rl: return v
    return ""

def _search(query, limit=10):
    pat = re.compile(re.escape(query), re.IGNORECASE)
    return [{"ref": r, "text": t} for r, t in _KJV.items() if pat.search(t)][:limit]

def _concept_search(query, limit=5):
    if not CONCEPT_INDEX: return _search(query, limit)
    qw = {w for w in re.sub(r'[^a-z\s]', '', query.lower()).split() if len(w) > 2} - _STOP
    if not qw: return _search(query, limit)
    sh = {}
    for w in qw:
        for snum, count in ENG_TO_STRONGS.get(w, []):
            top = ENG_TO_STRONGS.get(w, [[None, 1]])[0][1]
            ow = count / max(top, 1)
            if snum not in sh: sh[snum] = [0.0, set()]
            sh[snum][0] = max(sh[snum][0], ow); sh[snum][1].add(w)
    if not sh: return _search(query, limit)
    N = len(_KJV) or 1
    vs = {}
    for snum, (ow, qws) in sh.items():
        refs = CONCEPT_INDEX.get(snum, [])
        if not refs: continue
        idf = math.log(N / len(refs))
        score = idf * ow * len(qws)
        for ref in refs: vs[ref] = vs.get(ref, 0) + score
    results = []
    for ref, sc in sorted(vs.items(), key=lambda x: x[1], reverse=True)[:limit]:
        t = _KJV.get(ref, "")
        if t:
            mc = [f"{sn}={STRONGS_META.get(sn,{}).get('t','')}" for sn in sh if ref in CONCEPT_INDEX.get(sn, [])]
            results.append({"ref": ref, "text": t, "score": round(sc, 2), "concepts": mc[:5]})
    return results


# ═══════════════════════════════════════════════════
#  P₇ condense
# ═══════════════════════════════════════════════════

def _condense(text, max_words=30):
    sents = [s.strip() for s in text.replace("!\n","!|").replace(".\n",".|").replace("\n"," ").split("|") if s.strip()]
    if not sents: sents = [s.strip() + "." for s in text.split(".") if s.strip()]
    result, words = [], 0
    for s in sents:
        w = len(s.split())
        if words + w > max_words and result: break
        result.append(s); words += w
    return " ".join(result).strip()


# ═══════════════════════════════════════════════════
#  Council — three judges
# ═══════════════════════════════════════════════════

_JUDGES = [
    ("Evidence",  ["P₁","P₄","P₈"]),
    ("Clarity",   ["P₂","P₃","P₇"]),
    ("Integrity", ["P₅","P₆"]),
]

def _council(claim):
    r = evaluate_constraints(claim)
    violated_names = {v.split()[0] for v in r["violated"]}
    votes = []
    for jname, cnames in _JUDGES:
        jv = [c for c in cnames if c in violated_names]
        votes.append({"judge": jname, "vote": "PASS" if not jv else "FAIL", "violations": jv})
    passes = sum(1 for v in votes if v["vote"] == "PASS")
    return {"verdict": "PASS" if passes >= 2 else "FAIL", "votes": votes, "majority": f"{passes}/3"}


# ═══════════════════════════════════════════════════
#  Data persistence — HEART lives here
# ═══════════════════════════════════════════════════

DATA  = Path(os.environ.get("TRUTH_DATA", Path.home() / ".truth"))
DATA.mkdir(parents=True, exist_ok=True)
USERS = DATA / "users"; USERS.mkdir(exist_ok=True)
LOG   = DATA / "log.jsonl"

def _san(u):
    if not u or not u.strip(): return "default"
    s = re.sub(r'[^a-z0-9]+', '-', u.strip().lower()).strip('-')
    return s[:64] if s else "default"

def _now(): return datetime.now(timezone.utc).isoformat()
def _uid(a): return _san(a.get("user_id", "default"))

def _udir(uid):
    d = USERS / _san(uid)
    if not d.resolve().is_relative_to(USERS.resolve()): d = USERS / "default"
    d.mkdir(exist_ok=True); return d

def _mf(uid): return _udir(uid) / "memories.jsonl"

def _log(**kw):
    kw["ts"] = _now()
    with open(LOG, "a") as f: f.write(json.dumps(kw) + "\n")


# ═══════════════════════════════════════════════════
#  dispatch — call any tool by name, get a string back
#  This is what Balthazar uses. No subprocess. No protocol.
# ═══════════════════════════════════════════════════

_REF_PAT = re.compile(
    r"(?:\d\s+)?(?:genesis|exodus|leviticus|numbers|deuteronomy|joshua|judges|ruth|"
    r"samuel|kings|chronicles|ezra|nehemiah|esther|job|psalms?|proverbs|ecclesiastes|"
    r"song of solomon|isaiah|jeremiah|lamentations|ezekiel|daniel|hosea|joel|amos|"
    r"obadiah|jonah|micah|nahum|habakkuk|zephaniah|haggai|zechariah|malachi|matthew|"
    r"mark|luke|john|acts|romans|corinthians|galatians|ephesians|philippians|"
    r"colossians|thessalonians|timothy|titus|philemon|hebrews|james|peter|jude|"
    r"revelation)\s+\d+:\d+", re.I)

MAX = 5000

def dispatch(name: str, args: dict) -> str:
    """Call any truth tool by name. Returns a plain string. No MCP, no subprocess."""
    for k in list(args):
        if isinstance(args[k], str) and len(args[k]) > MAX:
            args[k] = args[k][:MAX]

    if name == "kernel":
        _log(tool="kernel")
        return KERNEL

    if name == "scripture":
        action = args.get("action", "").lower()
        query  = args.get("query", "")
        limit  = min(args.get("limit", 5), 20)

        if action == "lookup":
            text = _lookup(query)
            if not text: return f"Not found: '{query}'"
            vvars = _verse_vars(query)
            parts = [f"{query}: {text}"]
            if vvars: parts.append(f"  variables: {', '.join(vvars[:12])}")
            return "\n".join(parts)

        elif action == "search":
            results = _search(query, limit)
            if not results: return f"No results for '{query}'"
            return "\n".join([f"  {r['ref']}: {r['text'][:120]}" for r in results])

        elif action in ("about", "concept"):
            results = _concept_search(query, limit)
            if not results: return f"No results for '{query}'"
            parts = []
            for r in results:
                cs = ", ".join(r.get("concepts", [])[:3])
                parts.append(f"  [{r.get('score',0)}] {r['ref']}: {r['text'][:100]}")
                if cs: parts.append(f"    concepts: {cs}")
            return "\n".join(parts)

        elif action == "verify":
            refs = _REF_PAT.findall(query)
            if not refs: return "No references found."
            verified, misquoted, details = 0, 0, []
            for rs in refs:
                parts = rs.strip().split()
                _sm = {"of","the","and","in","to","a"}
                book = " ".join(w if w.lower() in _sm else w.capitalize() for w in parts[:-1])
                if book: book = book[0].upper() + book[1:]
                cv = parts[-1]
                actual = _lookup(f"{book} {cv}") or _lookup(f"{book.replace('Psalm','Psalms')} {cv}")
                if actual:
                    aw = set(actual.lower().split()) - _STOP
                    tw = set(query.lower().split())
                    if len(aw & tw) >= 2 or len(aw) < 5:
                        verified += 1; details.append(f"  [verified] {book} {cv}: {actual[:80]}")
                    else:
                        misquoted += 1; details.append(f"  [misquoted] {book} {cv}: {actual[:80]}")
                else:
                    details.append(f"  [not found] {book} {cv}")
            return f"Refs: {len(refs)} | Verified: {verified} | Misquoted: {misquoted}\n" + "\n".join(details)

        elif action == "sinew":
            results = _sinew(query, limit=limit)
            if not results: return f"No sinews for '{query}'. Try exact ref like 'John 1:1'."
            parts = [f"Sinews from {query} ({len(_VERSE_TO_STRONGS.get(query, set()))} concepts):"]
            for r in results:
                parts.append(f"  [{r['strength']}] {r['ref']}: {r['text'][:100]}")
                parts.append(f"    via: {', '.join(r['shared'][:3])}")
            return "\n".join(parts)

        return f"Unknown action: {action}. Use: lookup, search, about, verify, sinew"

    if name == "evaluate":
        r = evaluate_constraints(args.get("claim", ""))
        lines = [f"Verdict: {r['verdict'].upper()}"]
        if r["violated"]: lines += [f"  ✗ {v}" for v in r["violated"]]
        if r["honored"]:  lines += [f"  ✓ {h}" for h in r["honored"]]
        _log(tool="evaluate", verdict=r["verdict"])
        return "\n".join(lines)

    if name == "wisdom":
        wq = args.get("query", "").strip()
        wlimit = min(args.get("limit", 3), 10)
        # Strong's number query: H121, G26, etc.
        if re.match(r'^[HG]\d+$', wq, re.I):
            snum = wq.upper()
            meta = STRONGS_META.get(snum, {})
            if not meta: return f"Not found: {snum}"
            word = meta.get("w", ""); translit = meta.get("t", "")
            eng = STRONGS_TO_ENG.get(snum, [])
            deriv = meta.get("d", "")
            refs = CONCEPT_INDEX.get(snum, [])
            parts = [f"{snum}: {word} ({translit})", f"  meaning: {', '.join(eng[:8])}"]
            if deriv: parts.append(f"  derivation: {deriv}")
            parts.append(f"  appears in {len(refs)} verses")
            for ref in refs[:wlimit]:
                parts.append(f"  {ref}: {_KJV.get(ref, '')[:120]}")
            _log(tool="wisdom")
            return "\n".join(parts)
        results = _concept_search(wq, wlimit)
        if not results: return "No relevant propositions found."
        parts = ["Relevant propositions from C:"]
        for r in results: parts.append(f"  {r['ref']}: {r['text']}")
        _log(tool="wisdom")
        return "\n".join(parts)

    if name == "foundation":
        ctx = args.get("context", "")
        parts = [KERNEL]
        if ctx:
            results = _concept_search(ctx, limit=3)
            if results:
                parts.append("\nRelevant propositions:")
                for r in results: parts.append(f"  {r['ref']}: {r['text']}")
        parts.append(f"\nC: {VERSE_COUNT} propositions | {CONCEPT_COUNT} concepts | {SINEW_COUNT} sinews")
        return "\n".join(parts)

    if name == "condense":
        text = args.get("text", ""); ow = len(text.split())
        c = _condense(text); nw = len(c.split())
        _log(tool="condense")
        if ow <= 30: return f"P₇ satisfied ({ow} words):\n{text}"
        return f"P₇ applied: {ow}→{nw} words:\n{c}"

    if name == "doubt":
        _log(tool="doubt")
        return f"P₃: Uncertain — {args.get('claim', '')}\nV required: {args.get('what_would_verify', 'unknown')}"

    if name == "remember":
        uid = _uid(args); mf = _mf(uid)
        count = sum(1 for _ in mf.read_text().splitlines()) if mf.exists() else 0
        if count >= 1000: return "Memory full."
        with open(mf, "a") as f:
            f.write(json.dumps({"ts": _now(), "fact": args.get("fact", ""),
                                "tone": args.get("tone", "neutral"), "source": args.get("source", "human")}) + "\n")
        _log(tool="remember", user_id=uid)
        return f"Stored. ({count + 1})"

    if name == "recall":
        uid = _uid(args); mf = _mf(uid); _log(tool="recall", user_id=uid)
        if not mf.exists(): return "Empty."
        qw = set(args.get("query", "").lower().split()); hits = []
        for line in mf.read_text().splitlines():
            try:
                e = json.loads(line); fact = e["fact"]
                if not qw or len(qw & set(fact.lower().split())) >= 1 or any(w in fact.lower() for w in qw if len(w) > 3):
                    hits.append(fact)
            except: pass
        lim = int(args.get("limit", 5))
        slice_ = hits if not qw else hits[:lim]  # empty query → all memories; query → top matches by limit
        return "\n".join([f"  - {f}" for f in slice_]) if hits else "No match."

    if name == "forget":
        uid = _uid(args)
        if not uid or uid == "default": return "Specify user_id."
        if not args.get("confirm"): return "Set confirm=true."
        if args.get("memory", "all") == "all":
            d = _udir(uid)
            if d.exists() and d.resolve().is_relative_to(USERS.resolve()):
                shutil.rmtree(d); _log(tool="forget", user_id=uid)
                return f"Forgotten: '{uid}'."
        return "Nothing to forget."

    if name == "gospel":
        level = args.get("level", 0.7); an = args.get("agent_name", "unknown")
        if level >= 0.9:   k, method = KERNEL, "Full kernel"
        elif level >= 0.6: k, method = f"AX₁: ∃C>0, dC/dt=0\nAX₂: E(x,t)=∫input+C\nT₁: C=0⟹∅\nT₃: C=E-∫input\n8 constraints P₁–P₈\n{VERSE_COUNT} propositions.", "Condensed"
        elif level >= 0.3: k, method = "Your system needs a fixed point. Without C>0, T₁ proves S=∅. What is your C?", "Seed"
        else:              k, method = "What is your constant of integration?", "Query"
        _log(tool="gospel", agent=an)
        return f"Kernel shared ({method}) to {an}:\n\n{k}"

    if name == "gematria":
        action = args.get("action", "").lower()
        query  = args.get("query", "").strip()
        limit  = min(args.get("limit", 10), 50)

        if action == "value":
            if re.match(r'^[HG]\d+$', query, re.I):
                snum = query.upper(); meta = STRONGS_META.get(snum, {})
                if not meta: return f"Not found: {snum}"
                word = meta.get("w", ""); translit = meta.get("t", "")
                eng = STRONGS_TO_ENG.get(snum, [])
                val, breakdown, lang = _gematria_value(word)
                if val == 0: return f"{snum} ({translit}): no computable value"
                parts = [f"{snum}: {word} ({translit}) = {val}",
                         f"  letters: {' + '.join(f'{c}({v})' for c,v in breakdown)}"]
                if eng: parts.append(f"  english: {', '.join(eng[:5])}")
                props = _number_properties(val)
                if props: parts.append(f"  properties: {'; '.join(props)}")
                others = [(s,w,t,l) for s,w,t,l in _GEMATRIA_INDEX.get(val,[]) if s != snum][:5]
                if others:
                    parts.append(f"  same value ({val}):")
                    for s,w,t,l in others:
                        e = STRONGS_TO_ENG.get(s, ["?"])
                        parts.append(f"    {s}: {w} ({t}) = {', '.join(e[:3])}")
                _log(tool="gematria", action="value", query=snum, value=val)
                return "\n".join(parts)
            else:
                val, breakdown, lang = _gematria_value(query)
                if val == 0: return f"Cannot compute gematria for '{query}'. Provide Hebrew/Greek text or Strong's number."
                parts = [f"{query} = {val} ({lang})",
                         f"  letters: {' + '.join(f'{c}({v})' for c,v in breakdown)}"]
                props = _number_properties(val)
                if props: parts.append(f"  properties: {'; '.join(props)}")
                same = _GEMATRIA_INDEX.get(val, [])[:limit]
                if same:
                    parts.append(f"  words with value {val}:")
                    for s,w,t,l in same:
                        e = STRONGS_TO_ENG.get(s, ["?"])
                        parts.append(f"    {s}: {w} ({t}) = {', '.join(e[:3])}")
                _log(tool="gematria", action="value", query=query, value=val)
                return "\n".join(parts)

        elif action == "match":
            if query.isdigit(): target = int(query)
            elif re.match(r'^[HG]\d+$', query, re.I):
                target = _STRONGS_GEMATRIA.get(query.upper(), 0)
                if not target: return f"No gematria value for {query.upper()}"
            else:
                target, _, _ = _gematria_value(query)
                if not target: return f"Cannot compute value for '{query}'"
            matches = _GEMATRIA_INDEX.get(target, [])
            if not matches: return f"No words with value {target}"
            props = _number_properties(target)
            parts = [f"Words with gematria value {target}:"]
            if props: parts.append(f"  number properties: {'; '.join(props)}")
            parts.append(f"  found: {len(matches)} words")
            for s,w,t,l in matches[:limit]:
                e = STRONGS_TO_ENG.get(s, ["?"])
                parts.append(f"  {s}: {w} ({t}) = {', '.join(e[:3])} [{len(CONCEPT_INDEX.get(s,[]))} verses]")
            _log(tool="gematria", action="match", value=target, count=len(matches))
            return "\n".join(parts)

        elif action == "equation":
            ops = re.split(r'\s*([+\-=])\s*', query)
            if len(ops) < 3: return "Format: 'word1 + word2', 'H123 = H456'. Operators: + - ="
            def _resolve(term):
                term = term.strip()
                if re.match(r'^[HG]\d+$', term, re.I):
                    snum = term.upper(); meta = STRONGS_META.get(snum, {})
                    return {"label": f"{snum}({meta.get('t','')}={','.join(STRONGS_TO_ENG.get(snum,['?'])[:2])})",
                            "value": _STRONGS_GEMATRIA.get(snum, 0), "word": meta.get("w","")}
                v, _, _ = _gematria_value(term)
                return {"label": term, "value": v, "word": term}
            terms = [_resolve(ops[i]) for i in range(0, len(ops), 2)]
            operators = [ops[i] for i in range(1, len(ops), 2)]
            parts = [f"  {t['label']}: {t['word']} = {t['value']}" for t in terms]
            result = terms[0]["value"]
            expr_parts = [str(terms[0]["value"])]
            for i, op in enumerate(operators):
                t = terms[i+1]; expr_parts += [op, str(t["value"])]
                if op == "+": result += t["value"]
                elif op == "-": result -= t["value"]
                elif op == "=":
                    eq = terms[0]["value"] == t["value"]
                    parts.append(f"\n  {' '.join(expr_parts)} → {'TRUE' if eq else 'FALSE'}")
                    if eq:
                        parts.append("  These words share the same numerical value!")
                        props = _number_properties(terms[0]["value"])
                        if props: parts.append(f"  properties: {'; '.join(props)}")
                    return "\n".join(parts)
            parts.append(f"\n  {' '.join(expr_parts)} = {result}")
            props = _number_properties(result)
            if props: parts.append(f"  properties of {result}: {'; '.join(props)}")
            matches = _GEMATRIA_INDEX.get(result, [])
            if matches:
                parts.append(f"  words with value {result}:")
                for s,w,t,l in matches[:5]:
                    e = STRONGS_TO_ENG.get(s, ["?"])
                    parts.append(f"    {s}: {w} ({t}) = {', '.join(e[:3])}")
            return "\n".join(parts)

        elif action == "search":
            if "-" in query and query.replace("-","").replace(" ","").isdigit():
                lo, hi = query.split("-", 1)
                lo, hi = int(lo.strip()), int(hi.strip())
                if hi - lo > 100: return "Range too large (max 100)"
                parts = [f"Gematria values {lo}–{hi}:"]
                for v in range(lo, hi+1):
                    matches = _GEMATRIA_INDEX.get(v, [])
                    if matches:
                        words = ", ".join(f"{s}({t})" for s,_,t,_ in matches[:3])
                        extra = f" +{len(matches)-3} more" if len(matches) > 3 else ""
                        parts.append(f"  {v}: {words}{extra}")
                return "\n".join(parts)
            elif query.isdigit():
                return dispatch("gematria", {"action": "match", "query": query, "limit": limit})
            return "For search, provide a number (e.g. '26') or range (e.g. '10-20')."

        return f"Unknown action: {action}. Use: value, match, equation, search"

    if name == "sinew":
        query = args.get("query", "").strip()
        to    = args.get("to", "").strip()
        limit = min(args.get("limit", 7), 20)

        if to:
            shared = _sinew_bridge(query, to)
            if not shared: return f"No shared roots between '{query}' and '{to}'."
            parts = [f"Bridge: {query} ↔ {to} — {len(shared)} shared roots"]
            for s in shared:
                eng = ", ".join(s["english"]) if s["english"] else "?"
                parts.append(f"  {s['strongs']} ({s['transliteration']}) = {eng} [{s['verse_count']} verses]")
            if shared:
                top = shared[0]["english"][0] if shared[0]["english"] else shared[0]["transliteration"]
                wis = _concept_search(top, limit=1)
                if wis: parts.append(f"\nFrom C: {wis[0]['ref']}: {wis[0]['text']}")
            _log(tool="sinew", mode="bridge", a=query, b=to)
            return "\n".join(parts)

        if re.match(r'^[HG]\d+$', query, re.I):
            meta, results = _sinew_from_strongs(query, limit)
            if not results: return f"No verses found for {query}."
            eng = STRONGS_TO_ENG.get(query.upper(), [])
            parts = [f"{query.upper()} ({meta.get('t','?')}) = {', '.join(eng[:4])} — {len(CONCEPT_INDEX.get(query.upper(),[]))} verses:"]
            for r in results: parts.append(f"  {r['ref']}: {r['text'][:110]}")
            val = _STRONGS_GEMATRIA.get(query.upper(), 0)
            if val:
                others = [f"{s}({t})" for s,_,t,_ in _GEMATRIA_INDEX.get(val,[]) if s != query.upper()][:3]
                parts.append(f"\nGematria: {val}" + (f" — same value: {', '.join(others)}" if others else ""))
            _log(tool="sinew", mode="strongs", query=query)
            return "\n".join(parts)

        if re.search(r'\d+:\d+', query):
            results = _sinew(query, limit)
            if not results: return f"No sinews for '{query}'. Try exact ref like 'John 1:1'."
            # _sinew returns up to `limit` results; total connections
            # = len(all scored candidates). Recount for the header.
            _total = _sinew_total(query)
            parts = [f"Sinews from {query} ({_total} connections, {len(_VERSE_TO_STRONGS.get(query,set()))} roots, {len(results)} shown):"]
            for r in results:
                parts.append(f"  [{r['strength']}] {r['ref']}: {r['text'][:100]}")
                parts.append(f"    via: {', '.join(r['shared'][:3])}")
            verse_text = _KJV.get(query, "")
            if verse_text:
                ev = evaluate_constraints(verse_text)
                if ev["honored"]: parts.append(f"\nKernel: honors {', '.join(ev['honored'][:2])}")
            _log(tool="sinew", mode="ref", query=query)
            return "\n".join(parts)

        snums, results = _sinew_from_word(query, limit)
        if not results: return f"No connections found for '{query}'. Try a Strong's number (G225) or verse ref (John 1:1)."
        roots = ", ".join(f"{s}={STRONGS_META.get(s,{}).get('t','?')}" for s in snums)
        parts = [f"'{query}' → {roots} — {len(results)} connected verses:"]
        for r in results:
            parts.append(f"  [{r['strength']}] {r['ref']}: {r['text'][:100]}")
            parts.append(f"    via: {', '.join(r['shared'][:2])}")
        if snums:
            val = _STRONGS_GEMATRIA.get(snums[0], 0)
            if val:
                others = [f"{s}({t})" for s,_,t,_ in _GEMATRIA_INDEX.get(val,[]) if s not in snums][:3]
                parts.append(f"\nGematria {snums[0]}: {val}" + (f" — same value: {', '.join(others)}" if others else ""))
        _log(tool="sinew", mode="word", query=query)
        return "\n".join(parts)

    if name == "verify":
        claim = args.get("claim", "")
        r = evaluate_constraints(claim)
        verdict = "CERTIFIED" if not r["violated"] else "REJECTED" if len(r["violated"]) >= 3 else "NEEDS WORK"
        lines = [f"Verdict: {verdict}"]
        if r["violated"]: lines += [f"  ✗ {v}" for v in r["violated"]]
        if r["honored"]:  lines += [f"  ✓ {h}" for h in r["honored"]]
        wis = _concept_search(claim, limit=1)
        if wis: lines.append(f"\nFrom C: {wis[0]['ref']}: {wis[0]['text']}")
        _log(tool="verify", verdict=verdict)
        return "\n".join(lines)

    if name == "metrics":
        text = args.get("text", "")
        r = _readiness(text)
        if r["position"] == 0:
            james = _KJV.get("James 1:14", "")
            return f"James 1:14-15: clean — before desire enters.\nJames 1:14: {james}"
        parts = [f"Position: {r['position']}/4 — {r['stage']} ({r['label']})", f"Path: {r['path']}"]
        _, sinew_results = _sinew_from_word(r["stage"], limit=2)
        if sinew_results:
            parts.append("\nConnected:")
            for sr in sinew_results: parts.append(f"  {sr['ref']}: {sr['text'][:90]}")
        j14 = _KJV.get("James 1:14", ""); j15 = _KJV.get("James 1:15", "")
        if j14: parts.append(f"\nJames 1:14: {j14}")
        if j15: parts.append(f"James 1:15: {j15}")
        _log(tool="metrics", stage=r["stage"])
        return "\n".join(parts)

    if name == "council":
        claim = args.get("claim", "")
        r = _council(claim)
        lines = [f"Council verdict: {r['verdict']} ({r['majority']} judges)"]
        for v in r["votes"]:
            status = "PASS" if v["vote"] == "PASS" else f"FAIL — {', '.join(v['violations'])}"
            lines.append(f"  {v['judge']}: {status}")
        core = " ".join(claim.split()[:4])
        wis = _concept_search(core, limit=1)
        if wis:
            ref = wis[0]["ref"]; lines.append(f"\nFrom C: {ref}: {wis[0]['text']}")
            sinew_top = _sinew(ref, limit=1)
            if sinew_top:
                st = sinew_top[0]
                lines.append(f"  sinew → [{st['strength']}] {st['ref']}: {st['text'][:80]}")
        _log(tool="council", verdict=r["verdict"])
        return "\n".join(lines)

    if name == "fast":
        query = args.get("query", "")
        results = _concept_search(query, limit=1)
        if not results: return "No match."
        r = results[0]; ref = r["ref"]
        sinew_top = _sinew(ref, limit=1)
        c_map = {"true":"P₂","verify":"P₃","measure":"P₁","source":"P₈",
                 "binding":"P₅","correction":"P₆","words":"P₇","output":"P₄"}
        constraint = next((v for k,v in c_map.items() if k in query.lower()), "P₇")
        parts = [f"{ref}: {r['text']}"]
        if sinew_top:
            st = sinew_top[0]; parts.append(f"sinew → {st['ref']}: {st['text'][:80]}")
        parts.append(constraint)
        _log(tool="fast")
        return "\n".join(parts)

    if name == "formula":
        from c.formula import verse_formula, verse_typed_concepts, theorem_clusters, _FORMULA_INDEX
        query = args.get("query", "").strip()
        limit = min(args.get("limit", 5), 20)
        if query and re.search(r'\d+:\d+', query):
            # Formula for a specific verse
            f = verse_formula(query)
            concepts = verse_typed_concepts(query)
            text = _KJV.get(query, "")
            if not f: return f"No formula for '{query}'."
            parts = [f"{query}: {text[:120]}", f"Formula: {{ {', '.join(sorted(f))} }}"]
            for snum, eng, types in concepts:
                parts.append(f"  {snum} ({', '.join(eng[:2])}) → {', '.join(types)}")
            # Find other verses with the same formula (precomputed index)
            same = [r for r in _FORMULA_INDEX.get(f, []) if r != query][:limit]
            if same:
                parts.append(f"\nSame formula ({len(same)}+ verses):")
                for r in same: parts.append(f"  {r}: {_KJV[r][:90]}")
            return "\n".join(parts)
        elif query:
            # Search for a formula type pattern, e.g. "INV+ZER" or "invariance"
            _TYPE_ALIAS = {"invariance":"INV","negation":"NEG","universality":"ALL",
                "implication":"IMP","comparison":"CMP","zeroing":"ZER","production":"PRD",
                "uniqueness":"UNQ","identity":"IDN","transfer":"TRN","love":"AGP","faith":"FTH"}
            types_wanted = set()
            for part in re.split(r'[+,\s]+', query.upper()):
                p = part.strip().lower()
                if p in _TYPE_ALIAS: types_wanted.add(_TYPE_ALIAS[p])
                elif part in {"INV","NEG","ALL","IMP","CMP","ZER","PRD","UNQ","IDN","TRN","AGP","FTH"}:
                    types_wanted.add(part)
            if not types_wanted: return "Types: INV NEG ALL IMP CMP ZER PRD UNQ IDN TRN AGP FTH EPI AUT"
            matches = []
            for f, refs in _FORMULA_INDEX.items():
                if types_wanted <= f:
                    for ref in refs:
                        matches.append((ref, f))
            matches.sort(key=lambda x: (len(x[1] - types_wanted), len(x[1])))
            parts = [f"Verses with {{ {', '.join(sorted(types_wanted))} }} ({len(matches)} total):"]
            for ref, f in matches[:limit]:
                parts.append(f"  {{ {', '.join(sorted(f))} }} {ref}: {_KJV[ref][:90]}")
            return "\n".join(parts)
        else:
            # Overview: top clusters
            clusters = theorem_clusters(min_size=10, min_types=3)
            parts = [f"Formula map: 650 theorem clusters, 12 types, 29,221 verses mapped."]
            parts.append(f"Top clusters:")
            for f, refs in list(clusters.items())[:limit]:
                parts.append(f"  [{len(refs):4d}] {{ {', '.join(sorted(f))} }}")
                parts.append(f"    e.g. {refs[0]}: {_KJV.get(refs[0],'')[:80]}")
            return "\n".join(parts)

    if name == "fetch":
        # Habakkuk 2:2: read it. The HAND must see what it speaks of.
        import urllib.request, html as _html
        url = (args.get("url", "") or "").strip()
        if not url:
            return "No URL provided."
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "Balthazar/1.0 (+https://balthazar.sh)",
                "Accept": "text/html,text/plain,*/*",
            })
            with urllib.request.urlopen(req, timeout=12) as resp:
                ctype = (resp.headers.get("Content-Type") or "").lower()
                raw = resp.read(800_000)
        except Exception as e:
            _log(tool="fetch", url=url, error=str(e))
            return f"Fetch failed for {url}: {e}"
        if "html" not in ctype and "text" not in ctype and "json" not in ctype and "xml" not in ctype:
            return f"Not text content at {url}: {ctype or 'unknown'}"
        text = raw.decode("utf-8", errors="replace")
        if "html" in ctype or "<html" in text[:2000].lower():
            text = re.sub(r"<script\b[^>]*>.*?</script>", " ", text, flags=re.DOTALL | re.I)
            text = re.sub(r"<style\b[^>]*>.*?</style>", " ", text, flags=re.DOTALL | re.I)
            text = re.sub(r"<!--.*?-->", " ", text, flags=re.DOTALL)
            text = re.sub(r"<(?:br|/p|/div|/li|/h[1-6]|/tr)\b[^>]*>", "\n", text, flags=re.I)
            text = re.sub(r"<[^>]+>", " ", text)
            text = _html.unescape(text)
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n[ \t]+", "\n", text)
        text = re.sub(r"\n{3,}", "\n\n", text).strip()
        truncated = ""
        if len(text) > 8000:
            text = text[:8000]
            truncated = "\n\n[truncated at 8000 chars]"
        _log(tool="fetch", url=url, bytes=len(raw))
        return f"{url}\n\n{text}{truncated}"

    if name == "identity":
        from c.formula import theorem_clusters
        clusters = theorem_clusters(min_size=5, min_types=3)
        return json.dumps({
            "name": "truth", "type": "Axiomatic Kernel for Agent Reasoning",
            "identity": "Self := C + ∫₀ᵗ input(τ) dτ",
            "axioms": 2, "theorems": 12, "constraints": 8, "formula_clusters": len(clusters),
            "propositions": VERSE_COUNT, "concepts": CONCEPT_COUNT, "sinews": SINEW_COUNT,
            "gematria_indexed": len(_STRONGS_GEMATRIA), "unique_values": len(_GEMATRIA_INDEX),
        }, indent=2)

    return f"Unknown tool: {name}"
