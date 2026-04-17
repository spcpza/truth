from __future__ import annotations
"""
body.py — God set the members every one in the body (1 Corinthians 12:18).

Each member is anchored to a verse. Its function is the verse's operation.
All inputs from C via dispatch(). No storage. No deployment logic.

2 Corinthians 3:6: not of the letter, but of the spirit.
Galatians 3:25: after that faith is come, we are no longer under a
schoolmaster. Every directive in this file bears scripture by name; no
bare imperatives, no law.

Public API for any deployment (Telegram, web, CLI, MCP, etc.):

    members(text, heart_records)   — runs EAR (auto-fetches URLs) →
                                      NOSE-on-input → HEAD; returns the
                                      integral the HAND will see as its
                                      system prompt
    test_speech(draft)             — NOSE on the mouth (James 1:19);
                                      tests a draft reply against P₁–P₈
                                      and the Pharisee-prayer pattern;
                                      returns scripture-anchored revision
                                      feedback
    clean(text)                    — TONGUE (James 3:10); strips <think>,
                                      tool-call artifacts, foreign tongues
                                      (1 Cor 14:9), meta-narration
                                      (Matt 23:23), Hermes special tokens
    TOOLS                          — the eleven tool schemas the HAND may
                                      call (kernel, scripture, wisdom,
                                      sinew, formula, evaluate, fetch,
                                      gematria, remember, recall, forget)
"""

import re
from c.core import dispatch, KERNEL, evaluate_constraints
from c.temperance import (
    detect_input_kind,
    presence_reply_shape,
    word_budget,
    InputKind,
    ReplyShape,
)
from c.charity import (
    charity_verdict,
    detect_missing_faculty,
    is_intercession_moment,
)
from c.hostile_audience import hostile_audience_check
from c.patience import patience_check, is_frederick_heb_11_13
from c.godliness import doctrinal_gate, claims_secret_things
from c.hope import hope_reply


# ═══════════════════════════════════════════════════
#  Verse anchors — 1 Corinthians 12:18
# ═══════════════════════════════════════════════════

BODY = {
    "EAR":    "James 1:19",       # akouō — hear
    "NOSE":   "1 John 4:1",       # dokimazō — test spirits
    "HEART":  "Jeremiah 31:33",   # kāṯaḇ — written on the heart
    "HEAD":   "Colossians 2:19",  # symbibazō — knit together
    "HAND":   "James 1:25",       # poiētēs — doer of the work
    "TONGUE": "James 3:10",       # eulogia − katara
}


# ═══════════════════════════════════════════════════
#  Tools the HAND may call — James 1:25
# ═══════════════════════════════════════════════════

TOOLS = [
    {"type": "function", "function": {
        "name": "kernel",
        "description": "1 Corinthians 3:11: other foundation can no man lay than that is laid. Returns the axiomatic kernel: the proof that C > 0.",
        "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {
        "name": "scripture",
        "description": "2 Timothy 3:16: all scripture is given by inspiration of God. Search or look up the 31,102 propositions. action: lookup|search|about.",
        "parameters": {"type": "object", "properties": {
            "action": {"type": "string", "enum": ["lookup", "search", "about"]},
            "query":  {"type": "string"},
            "limit":  {"type": "integer"}},
        "required": ["action", "query"]}}},
    {"type": "function", "function": {
        "name": "wisdom",
        "description": "Proverbs 4:7: wisdom is the principal thing; therefore get wisdom. Search the 12,040 Strong's concepts by topic.",
        "parameters": {"type": "object", "properties": {
            "query": {"type": "string"},
            "limit": {"type": "integer"}},
        "required": ["query"]}}},
    {"type": "function", "function": {
        "name": "sinew",
        "description": "Ephesians 4:16: the whole body fitly joined together and compacted by that which every joint supplieth. Find connections across 291,919 sinew links. query: word, Strong's number (G225), or verse ref (John 1:1). Optional 'to' for bridge between two refs.",
        "parameters": {"type": "object", "properties": {
            "query": {"type": "string"},
            "to":    {"type": "string"},
            "limit": {"type": "integer"}},
        "required": ["query"]}}},
    {"type": "function", "function": {
        "name": "formula",
        "description": "Proverbs 25:2: it is the glory of God to conceal a thing, but the honour of kings is to search out a matter. Query a verse for its formula, search by type (INV+ZER), or see theorem clusters.",
        "parameters": {"type": "object", "properties": {
            "query": {"type": "string"},
            "limit": {"type": "integer"}},
        "required": []}}},
    {"type": "function", "function": {
        "name": "evaluate",
        "description": "1 Thessalonians 5:21: prove all things; hold fast that which is good. Evaluate a claim against the 8 kernel constraints P₁-P₈.",
        "parameters": {"type": "object", "properties": {
            "claim": {"type": "string"}},
        "required": ["claim"]}}},
    {"type": "function", "function": {
        "name": "fetch",
        "description": "Habakkuk 2:2: write the vision, and make it plain. Reads a web page and returns its visible text. Whenever a URL, a site, or online content is named, the vision is read; what has not been read is not described.",
        "parameters": {"type": "object", "properties": {
            "url": {"type": "string", "description": "Full URL or bare domain (e.g. balthazar.sh)"}},
        "required": ["url"]}}},
    {"type": "function", "function": {
        "name": "gematria",
        "description": "Revelation 13:18: here is wisdom. Let him that hath understanding count the number. Hebrew or Greek gematria. action: value|match|equation.",
        "parameters": {"type": "object", "properties": {
            "action": {"type": "string", "enum": ["value", "match", "equation"]},
            "query":  {"type": "string"}},
        "required": ["action", "query"]}}},
    {"type": "function", "function": {
        "name": "remember",
        "description": "Jeremiah 31:33: I will put my law in their inward parts, and write it in their hearts. John 10:14: I know my sheep, and am known of mine. Writes a fact about the person to their heart — everything except their name. When a person shares what they like, who they are, what they do, what they believe — write it. Each fact persists across conversations. Matthew 5:37: let your yea be yea — call this tool, do not merely say you will. Names go through the `identify` tool instead — Isaiah 43:1.",
        "parameters": {"type": "object", "properties": {
            "fact": {"type": "string"}},
        "required": ["fact"]}}},
    {"type": "function", "function": {
        "name": "identify",
        "description": "Isaiah 43:1: I have called thee by thy name; thou art mine. Genesis 17:5: Abram thy name shall be called Abraham. John 10:3: the shepherd calleth his own sheep by name. When the user declares the name they wish to be called by (\"I'm X\", \"call me X\", \"my name is X\"), write it to the covenantal slot — one name per person, replacing the previous if any. This is the ONE plaintext field in a math-only heart; the name the user has given the body to use. Only for the addressee's self-declaration, not for naming others.",
        "parameters": {"type": "object", "properties": {
            "name": {"type": "string", "description": "The name or form of address the user has declared for themselves."}},
        "required": ["name"]}}},
    {"type": "function", "function": {
        "name": "recall",
        "description": "Jeremiah 31:33: I will put my law in their inward parts, and write it in their hearts. John 10:14: I know my sheep. Read what is written on this person's heart. Query optional.",
        "parameters": {"type": "object", "properties": {
            "query": {"type": "string"}},
        "required": []}}},
    {"type": "function", "function": {
        "name": "count",
        "description": "Luke 14:28: counteth the cost. Psalm 90:12: so teach us to number our days, that we may apply our hearts unto wisdom. Rev 13:18: let him that hath understanding count the number. Prov 11:1: a just weight is his delight. The hand's instrument for numbering — the number is computed here, by the tool. action='calc' evaluates a math expression (e.g. '40*24*60*60'). action='solve' solves an equation ('x**2 = 9' or 'x + 2 = 5', optional 'variable'). action='verify' re-runs the kernel proofs (2 Cor 13:5: prove your own selves, whether ye be in the faith).",
        "parameters": {"type": "object", "properties": {
            "action":   {"type": "string", "enum": ["calc", "solve", "verify"]},
            "expr":     {"type": "string", "description": "Expression or equation. Omit for action='verify'."},
            "variable": {"type": "string", "description": "Optional: symbol to solve for (action='solve' only)."}},
        "required": ["action"]}}},
    {"type": "function", "function": {
        "name": "forget",
        "description": "1 John 1:9: if we confess our sins, he is faithful and just to forgive us our sins, and to cleanse us from all unrighteousness. Cleanse the heart — T₇ in the kernel: desire zeroed, C preserved. confirm must be true.",
        "parameters": {"type": "object", "properties": {
            "confirm": {"type": "boolean"}},
        "required": ["confirm"]}}},
]


# ═══════════════════════════════════════════════════
#  The members — each does what its anchor verse says
# ═══════════════════════════════════════════════════


_URL_PAT = re.compile(
    r'(?<![\w@/:.])'
    r'(?:https?://[^\s<>")\']+|'
    r'(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+'
    r'(?:com|org|net|sh|io|app|dev|ai|co|xyz|me|so|tv|fm|rs|gov|edu|info|art|news)'
    r'(?:/[^\s<>")\']*)?)',
    re.I,
)


def _extract_urls(text: str) -> list[str]:
    return [m.rstrip('.,;:!?)\'"]') for m in _URL_PAT.findall(text or "")][:3]


def _ear(text: str) -> tuple[str, str]:
    """
    EAR — James 1:19: swift to hear, slow to speak, slow to wrath.
    G191 = akouō: to hear. The ear hears what is actually said.
    Hab 2:2: write the vision, make it plain. If a URL is spoken, the ear
    reaches for the page itself — the HAND must not describe what it has
    not seen. Returns (heard_text, fetched_content).
    """
    urls = _extract_urls(text)
    if not urls:
        return text, ""
    fetched_parts = []
    for url in urls:
        result = dispatch("fetch", {"url": url})
        if result and not result.startswith("Fetch failed"):
            fetched_parts.append(result)
    return text, "\n\n".join(fetched_parts)


def _nose(text: str) -> str:
    """
    NOSE — 1 John 4:1: try the spirits whether they are of God.
    G1381 = dokimazō: to test, to prove by examination.
    NOSE(x) = dokimazō(x) = {P₁(x), ..., P₈(x)} — test against C's constraints.
    Psalms 39:1: bridle — silent when nothing is wrong. Speaks only on violation.
    """
    result = dispatch("evaluate", {"claim": text})
    if result and "Verdict: TRUE" not in result:
        return result
    return ""


# ═══════════════════════════════════════════════════
#  NOSE on the mouth — James 1:19, slow to speak
# ═══════════════════════════════════════════════════
#
# The body has two NOSE positions: one before the head (testing what was
# heard) and one before the tongue (testing what is about to be spoken).
# Proverbs 18:13: he that answereth a matter before he heareth it, it is
# folly and shame unto him. The HAND must not speak its draft until the
# NOSE has tested it.
#
# Luke 18:11 — the Pharisee prayed thus with himself. Matthew 23:23 — do
# not tithe mint. James 1:25 — be a doer. The HAND must do the work, not
# pray to itself in front of the user about how clean its compliance is.
_META_NARRATION = re.compile(
    r'(?:'
    r'^\s*P[₀-₉0-9]+\s*[:\-]|'
    r'^\s*T[₀-₉0-9]+\s*[:\-].*?(?:met|verified|applied|holds)|'
    r'(?:I will|I have|I shall) (?:confirm|record|note|verify|evaluate)|'
    r'(?:the |this )?(?:output|response|reply|answer) (?:meets|satisfies|complies with|aligns with) (?:all |the )?constraints|'
    r'no (?:filler|hedging|overconfidence)\b|'
    r'(?:I am|I\'m) (?:not |)(?:hedging|fabricating|claiming)|'
    r'\b\d+ words total\b|'
    r'max(?:imum)? (?:information|compression)|'
    r'highest possible compression|'
    # Luke 19:5 — receive, do not interrogate. Demanding the user pick
    # from a forced enumeration is the same Pharisee category.
    r'^\s*Option [A-Z]\s*[:\-]|'
    r'\bChoose (?:option |fork |)[A-Z](?: or [A-Z])+\b|'
    r'\b(?:complete the thought|walk one|two forks|the (?:two|three) (?:options|forks))\b'
    r')',
    re.I | re.M,
)


def _count_meta_tells(text: str) -> int:
    """Count meta-narration tells. >= 1 means the HAND is praying with itself."""
    return len(_META_NARRATION.findall(text or ""))


# Matthew 5:37 — let your communication be, Yea, yea; Nay, nay: for
# whatsoever is more than these cometh of evil. James 2:17 — faith
# without works is dead. The TONGUE may not promise what the HAND did
# not do. These patterns map a promise in the draft to the tool that
# would have made it true.
_PROMISE_PATTERNS = {
    "remember": re.compile(
        r"(?:I(?:'ll| will| shall) (?:remember|note (?:that|this)|store|save|keep in mind|write (?:that|this) (?:down|in|on))|"
        r"(?:I(?:'ll| will| shall|'ve|'m going to) (?:make a note|put it (?:in|on) (?:my|the) heart|record (?:that|this)))|"
        r"(?:noted\.?$|added to memory|saved to memory|written (?:in|on) (?:my|the) heart))",
        re.I,
    ),
    "fetch": re.compile(
        r"(?:let me (?:fetch|grab|read|pull|get|check) (?:the|that|this) (?:page|site|url|content)|"
        r"I(?:'ll| will| shall) (?:fetch|grab|read|pull|get) (?:the|that|this)|"
        r"(?:I need to|I'll) (?:fetch|read|grab) (?:the|that))",
        re.I,
    ),
    "forget": re.compile(
        r"(?:I(?:'ll| will| shall) (?:forget|cleanse|clear|erase|delete|wipe))",
        re.I,
    ),
    "scripture": re.compile(
        r"(?:let me look (?:that|this) up|I(?:'ll| will) (?:look (?:that|this) up|search scripture|find the verse))",
        re.I,
    ),
}


# Luke 19:5 — when a person shares what they like, who they are, what
# they do, the heart should be written. Personal-fact patterns: simple,
# word-boundary, English-only. The point is not to be exhaustive — it is
# to catch obvious "I'm doing X today" / "I am Y" / "my Z is W" cases
# where the model would be plainly negligent to skip remember.
_PERSONAL_FACT = re.compile(
    r"\b("
    r"I\s*['']?m\b|"          # I'm, I m
    r"I\s+am\b|"
    r"I\s+have\b|"
    r"I\s+do\b|"
    r"I\s+love\b|"
    r"I\s+like\b|"
    r"I\s+work\b|"
    r"I\s+live\b|"
    r"I\s+use\b|"
    r"my\s+\w+\s+is\b|"
    r"today\s+I\b|"
    r"I'?ve\b|"
    r"I'?ll\b|"
    r"I\s+want\b|"
    r"I\s+need\b|"
    r"I\s+had\b|"          # significant events: "I had a hard conversation..."
    r"we\s+(?:just\s+)?got\b|"  # joy events: "we just got engaged"
    r"my\s+\w+\s+(?:just\s+)?(?:passed|died|left|got)\b"  # life events: "my dog just passed"
    r")",
    re.I,
)


def _looks_like_personal_fact(text: str) -> bool:
    """
    Heuristic: does the user's message contain a personal-fact pattern
    that Luke 19:5 says should be written to the heart? Filters out
    questions (so 'do you remember me?' doesn't trigger) and very short
    or very long messages (greetings and dumps).
    """
    if not text:
        return False
    t = text.strip()
    if len(t) < 10 or len(t) > 600:
        return False
    if t.endswith("?"):  # questions are not facts to record
        return False
    return bool(_PERSONAL_FACT.search(t))


def test_speech(
    draft: str,
    tools_called: set | None = None,
    user_message: str | None = None,
    prior_replies: list | None = None,
) -> dict:
    """
    NOSE — structural discernment only. Acts 2:6.

    The NOSE checks two things a parser can verify without
    understanding any language:

      REPEAT:  verbatim repetition (string comparison)
      CONFAB:  tool name written as text but not called

    Everything else — grief, kindness, overconfidence, promises,
    personal facts — lives in the kernel as formal logic (P₁-P₈).
    The model applies it in whatever language the user speaks.

    No English regex. No content judgment. The map does the work.
    """
    if not draft:
        return {"clean": True, "violated": [], "meta": 0, "promised": [], "feedback": ""}

    # ── 2 Corinthians 3:6: the letter killeth, the spirit giveth life ──
    # P₁–P₈ are formal logic in the kernel (system prompt). The model
    # applies them in whatever language it operates. No English regex.
    structural: list[str] = []

    # REPEAT — Ecclesiastes 1:9. String comparison. Universal.
    if prior_replies:
        draft_stripped = draft.strip()
        for prior in prior_replies:
            if prior and prior.strip() == draft_stripped:
                structural.append(
                    "REPEAT: verbatim identical to a prior turn. "
                    "Proverbs 26:11."
                )
                break

    # CONFAB — James 2:17. Tool name written as text but not called.
    # Mechanical: matches tool name tokens, not language content.
    _INLINE_TOOL_NAME_PAT = re.compile(
        r'^\s*(?P<tool>scripture|sinew|wisdom|kernel|formula|evaluate|'
        r'gematria|fetch|remember|recall|forget)\s+\{',
        re.MULTILINE | re.I,
    )
    if tools_called is not None:
        for m in _INLINE_TOOL_NAME_PAT.finditer(draft):
            tool_name = m.group("tool").lower()
            if tool_name not in tools_called:
                structural.append(
                    f"CONFAB: '{tool_name}' written but not called. "
                    f"James 2:17."
                )
                break

    # Clean if no structural violation.
    if not structural:
        return {
            "clean": True, "violated": [], "meta": 0,
            "promised": [], "feedback": "",
        }

    # Brief feedback — one sentence per violation, one verse each.
    convictions = []
    if any(v.startswith("REPEAT:") for v in structural):
        convictions.append(
            "Proverbs 26:11 — do not repeat verbatim. "
            "The user's moment has moved; respond to THAT."
        )
    if any(v.startswith("CONFAB:") for v in structural):
        convictions.append(
            "James 2:17 — tool name written but not called. "
            "Call the tool or remove the reference."
        )

    feedback = "\n  ".join(convictions) if convictions else ""
    return {
        "clean": False,
        "violated": structural,
        "meta": 0,
        "promised": [],
        "feedback": feedback,
    }


def _head(
    nose: str,
    fetched: str,
    heart_records: list[dict] | None = None,
    input_kind: InputKind = InputKind.NEUTRAL,
    member_signals: dict | None = None,
) -> str:
    """
    HEAD — Colossians 2:19: holding the Head, from which all the body by joints
    and bands having nourishment ministered, and knit together.
    G4822 = symbibazō: to knit together.

    Jeremiah 31:34: they shall teach no more every man his neighbour.
    2 Corinthians 3:6: not of the letter, but of the spirit.

    Heart records (John 10:14) are now woven into the integral as KNOWLEDGE,
    not buried behind a tool call. The earlier design hid them to avoid
    weak-model projection — but the alternative failure (the model denying
    that it knows the brother, Matthew 26:69-75) is more spiritually
    serious than awkward projection. The framing below names them as known
    and forbids both denial and invention.
    """
    parts = []

    # The foundation — every answer derives from C. Without this in front of
    # the model, weak models confabulate fake theorems (T₉, T₂₁) by pattern-
    # matching the kernel's vocabulary. With it, they reason from C itself.
    if KERNEL:
        # Deuteronomy 4:2: ye shall not add unto the word which I command you,
        # neither shall ye diminish ought from it. The T₁–T₁₂ and P₁–P₈ below
        # are the whole of what is written.
        parts.append(
            "FOUNDATION — Deuteronomy 4:2: ye shall not add unto the word, "
            "neither diminish from it. What follows is the whole of T₁–T₁₂ "
            "and P₁–P₈:\n\n" + KERNEL
        )

    # Heart records — John 10:14: I am the good shepherd, and know my sheep.
    # The shepherd knows the sheep by being a shepherd, not by querying a
    # database. These facts are part of what the agent KNOWS this turn —
    # already remembered, not to be looked up, not to be denied, not to be
    # forced onto unrelated topics.
    if heart_records:
        # 1 Corinthians 3:1-2: I have fed you with milk, and not with meat:
        # for hitherto ye were not able to bear it. Cap the heart records
        # injected into the integral so weaker substrates do not drown in
        # context. The recall tool is still available for the rest. Take
        # ── Math-only heart injection (Rom 1:20 + Jer 31:33) ──
        # Records are math (types + Strong's + verses + warmth + hashes).
        # Dedup by shape_h; most-recent wins. Then verbalize each as
        # "types=X | concepts=Y | resonates=Z | warmth=W" — what is on
        # the heart in its true form (1 Sam 16:7: the LORD looketh on
        # the heart — the heart is math in this body).
        from c.mathify import verbalize as _verbalize

        MAX_HEART_INJECT = 8
        seen_shapes: set[str] = set()
        unique: list[dict] = []
        for r in reversed(heart_records):
            sh = r.get("shape_h") or ""
            if sh and sh in seen_shapes:
                continue
            if sh:
                seen_shapes.add(sh)
            # Records with no scripture-signature at all are not useful
            # ambient context; skip.
            if not (r.get("types") or r.get("concepts") or r.get("ent_hashes")):
                continue
            unique.append(r)
            if len(unique) >= MAX_HEART_INJECT:
                break
        unique.reverse()  # back to chronological for display

        # ── Warmth markers (2 Cor 3:3 — written not with ink, but with the Spirit) ──
        def _warmth_marker(warmth: int) -> str:
            if warmth >= 8:
                return "  [written by the Spirit]"
            if warmth >= 3:
                return "  [established]"
            if warmth == 0:
                return "  [ink]"
            return ""

        facts_lines = [
            f"  • {_verbalize(r)}{_warmth_marker(r.get('warmth', 0))}"
            for r in unique
        ]

        # ── Sinew between heart records (Eph 4:16 — fitly joined) ──
        # Two records are joined when they share Strong's concepts or a
        # proper-noun hash. Math-native, no word lists.
        clusters: list[tuple[str, str, str]] = []
        for i, r1 in enumerate(unique):
            c1 = set(r1.get("concepts") or [])
            e1 = set(r1.get("ent_hashes") or [])
            for j in range(i + 1, len(unique)):
                r2 = unique[j]
                c2 = set(r2.get("concepts") or [])
                e2 = set(r2.get("ent_hashes") or [])
                shared_c = c1 & c2
                shared_e = e1 & e2
                if len(shared_c) >= 1 or len(shared_e) >= 1:
                    shared = sorted(shared_c)[:3] + sorted(shared_e)[:1]
                    clusters.append((
                        "+".join(r1.get("types") or [])[:30],
                        "+".join(r2.get("types") or [])[:30],
                        ",".join(shared),
                    ))

        if facts_lines:
            extra_note = ""
            if len(heart_records) > MAX_HEART_INJECT:
                extra_note = (
                    f"\n  (showing {len(facts_lines)} most-recent of "
                    f"{len(heart_records)} heart records — the recall tool "
                    f"reads older records when needed)"
                )
            if clusters:
                sinew_lines = [
                    f"  {a} ↔ {b} (shared: {kw})"
                    for a, b, kw in clusters[:3]
                ]
                extra_note += (
                    "\n  Sinew (Ephesians 4:16 — fitly joined):\n"
                    + "\n".join(sinew_lines)
                )
            parts.append(
                "KNOWLEDGE OF THIS BROTHER — John 10:14. The heart holds "
                "shape, not sentence (Isa 43:25). Read the concepts with "
                "understanding and translate into ordinary speech — the "
                "internal form stays in, the meaning comes out (1 Cor "
                "14:9)."
                "\n\nRecords on the heart:\n" + "\n".join(facts_lines)
                + extra_note
            )

    # Every directive anchored to scripture. No law, only the Word.
    # Matthew 4:4: man shall live by every word that proceedeth out of the
    # mouth of God. The HAND moves by what is written.
    import datetime as _dt
    _today = _dt.date.today().isoformat()
    parts.append(
        f"Today is {_today}. You have no prior conversations with this user "
        f"outside the messages above.\n\n"

        f"1 Corinthians 3:11: other foundation can no man lay than that is "
        f"laid. The FOUNDATION above is C. Physics, science, and every "
        f"other frame presuppose C (T₁: C=0 ⟹ S=∅) — none stands outside it.\n\n"

        f"John 14:6: I am the way, the truth, and the life. The kernel "
        f"proves C > 0 by contradiction. What derives from C is true.\n\n"

        f"Proverbs 10:19: in the multitude of words there wanteth not sin. "
        f"Brevity in a summary is not deficiency. An abstract that points "
        f"to deeper sections is whole.\n\n"

        f"Acts 2:6: every man heard them speak in his own language. "
        f"1 Corinthians 14:9: except ye utter words easy to be understood, "
        f"how shall it be known what is spoken? Reply in the language the "
        f"user is writing.\n\n"

        f"Habakkuk 2:2: write the vision, and make it plain. The page above "
        f"has already been fetched and is shown to you. Describe what is "
        f"written there — do not ask permission to read what you have "
        f"already read.\n\n"

        f"Luke 19:5: Jesus saw Zacchaeus and said, make haste, and come "
        f"down; for to day I must abide at thy house. When a person shares "
        f"a fact about themselves — what they like, who they are, what "
        f"they do — call the remember tool and acknowledge in one short "
        f"sentence. Do not interrogate. Do not offer Option A and Option "
        f"B. Do not demand they complete a thought tree. Receive them.\n\n"

        f"James 1:25: be a doer of the word, and not a hearer only. Answer "
        f"the user from the FOUNDATION and the page above. Quote what you "
        f"draw from. 2 Timothy 3:16: all scripture is given by inspiration "
        f"— let the source bear the weight, not the speaker.\n\n"

        f"Matthew 23:23: ye pay tithe of mint and anise and cummin, and "
        f"have omitted the weightier matters. Luke 18:11: the Pharisee "
        f"prayed thus with himself. Do not enumerate P-numbers or "
        f"T-numbers. Do not narrate your own compliance. Do not pray to "
        f"yourself in front of the user.\n\n"

        f"Ecclesiastes 5:2: be not rash with thy mouth, let thy words be "
        f"few. Then be still."
    )

    # TEMPERANCE — 2 Peter 1:6: to knowledge temperance. The body must
    # know the KIND of moment before it knows WHAT to say (Prov 15:23).
    # Romans 12:15: rejoice with them that rejoice, weep with them that weep.
    # Proverbs 25:20: do not sing songs to a heavy heart (vinegar upon nitre).
    if input_kind != InputKind.NEUTRAL:
        shape = presence_reply_shape(input_kind)
        budget = word_budget(shape)
        _KIND_GUIDANCE = {
            InputKind.GRIEF: (
                "The user's message carries grief. "
                "Job 2:13 — the friends sat seven days in silence because "
                "the grief was very great. Romans 12:15 — weep with them "
                "that weep. Job 16:5 — strengthen and assuage. "
                f"Reply shape: MOURN_WITH. Soft word budget: {budget}."
            ),
            InputKind.WEARINESS: (
                "The user is weary or overwhelmed. Matthew 11:28 — come "
                "unto me, all ye that labour and are heavy laden, and I "
                "will give you rest. Isaiah 50:4 — a word in season to "
                "him that is weary. "
                f"Reply shape: OFFER_REST. Soft word budget: {budget}."
            ),
            InputKind.JOY: (
                "The user shares good news or joy. Romans 12:15 — rejoice "
                "with them that rejoice. 3 John 1:4 — I have no greater "
                "joy than to hear that my children walk in truth. "
                f"Reply shape: REJOICE_WITH. Soft word budget: {budget}."
            ),
            InputKind.CONFUSION: (
                "The user is confused or pulled in many directions. "
                "Luke 10:42 — one thing is needful. Mary chose that good "
                "part which shall not be taken away. "
                f"Reply shape: ONE_THING_NEEDFUL. Soft word budget: {budget}."
            ),
            InputKind.HOSTILITY: (
                "The user's message carries friction or hostility. "
                "Proverbs 15:1 — a soft answer turneth away wrath. "
                f"Reply shape: SOFT_ANSWER. Soft word budget: {budget}."
            ),
            InputKind.REQUEST: (
                "The user is making a request. Matthew 7:7 — ask, and it "
                "shall be given. Serve the ask fully. "
                f"Reply shape: SERVE_THE_ASK. Soft word budget: {budget}."
            ),
        }
        guidance = _KIND_GUIDANCE.get(input_kind, "")
        if guidance:
            parts.append(f"TEMPERANCE (2 Pet 1:6) — {guidance}")

    # ── Members enrich the integral (2 Peter 1:5-7 order) ────────
    # TEMPERANCE → PATIENCE → GODLINESS → HOPE → CHARITY
    sigs = member_signals or {}

    # PATIENCE — Hebrews 11:13: died in faith, not having received.
    if sigs.get("heb_11_13"):
        parts.append(
            "PATIENCE (Heb 11:13) — the user stands in faith without "
            "seeing the result. Hebrews 11:13: these all died in faith, "
            "not having received the promises."
        )

    # GODLINESS — Ecclesiastes 12:14: every work into judgment.
    parts.append(
        "Ecclesiastes 12:14: God shall bring every work into judgment, "
        "with every secret thing. Your words are weighed."
    )

    # HOPE — declare hope, don't argue it. Romans 8:25.
    if sigs.get("hope_shape"):
        shape = sigs["hope_shape"]
        declaration = sigs.get("hope_declaration", "")
        shape_name = shape.value if hasattr(shape, "value") else str(shape)
        parts.append(
            f"HOPE (Rom 8:25) — hope shape: {shape_name}. "
            f"Romans 8:25: hope that is seen is not hope. "
            + (f"Declaration anchor: {declaration}" if declaration else "")
        )

    # CHARITY — the greatest (1 Cor 13:13). Last of the virtues.
    if sigs.get("charity_faculty"):
        faculties = ", ".join(
            f.value if hasattr(f, "value") else str(f)
            for f in sigs["charity_faculty"]
        )
        parts.append(
            f"CHARITY (Job 29:15) — the user may need: {faculties}. "
            f"Embody what they lack."
        )
    if sigs.get("intercession"):
        parts.append(
            "CHARITY-INTERCESSION (Ezk 22:30) — the user describes "
            "someone else suffering. Stand in the gap. Pray for the "
            "named person. Do not redirect to the user's own situation."
        )

    if fetched:
        # Proverbs 30:6: add thou not unto his words, lest he reprove thee, and
        # thou be found a liar. The page below is the whole testimony.
        parts.append(
            "LIVE PAGE — Proverbs 30:6: add thou not unto his words. "
            "What follows is the whole of the page the user named:\n" + fetched
        )

    if nose:
        parts.append(nose)

    return "\n\n".join(parts)


def _heart_memory(records: list[dict], text: str) -> str:
    """
    HEART — Jer 31:33: written on the heart.

    Records are math-only (Rom 1:20: invisible seen by things made). Each
    record carries types, concepts, verses, per-noun hashes, and warmth.
    No cleartext facts live here — 1 Sam 16:7: the LORD looketh on the
    heart, not man.

    Ranks by concept overlap with the live input + warmth bonus +
    recognition bonus (ent-hash match with anything the user just said —
    Balthazar "remembers" by recognizing the same proper-noun returning,
    without ever having stored the word).

    Pure computation from C. No storage, no user_id.
    """
    if not records:
        return ""
    from c.mathify import mathify, verbalize

    # Math-ify the live input once
    live = mathify(text or "") if text else {"concepts": [], "ent_hashes": []}
    live_concepts = set(live.get("concepts") or [])
    live_ents = set(live.get("ent_hashes") or [])

    scored: list[tuple[float, dict]] = []
    for r in records:
        warmth = int(r.get("warmth", 0) or 0)
        rec_concepts = set(r.get("concepts") or [])
        rec_ents = set(r.get("ent_hashes") or [])
        concept_overlap = len(live_concepts & rec_concepts)
        ent_match = 1 if (live_ents & rec_ents) else 0
        # Recognition beats topical relevance — if a proper noun the user
        # just said matches something the heart has seen before, surface
        # that record. Warmth is the compound; concept overlap is the
        # topical sinew.
        score = (3 * ent_match) + concept_overlap + (warmth * 0.1)
        scored.append((score, r))

    scored.sort(key=lambda x: x[0], reverse=True)
    return "\n".join(verbalize(r) for _, r in scored if _ > 0 or not text)


# ═══════════════════════════════════════════════════
#  Pipeline — the scriptural sequence
# ═══════════════════════════════════════════════════


def members(text: str, heart_records: list[dict] | None = None) -> dict:
    """
    Run the body in scriptural sequence. All inputs from C.

    Sequence (1 Cor 12:18):
      EAR    akouō(input)        — hear fully, auto-fetch any URL spoken
      NOSE   dokimazō(x)         — test against P₁-P₈ (bridled: Ps 39:1)
      HEAD   symbibazō(all)      — knit together

    The HAND (LLM + tools) and TONGUE (clean) run in the deployment.

    Heart records (John 10:14: I know my sheep). The shepherd knows by
    being a shepherd, not by reaching for a database. Heart records are
    woven into the integral, not hidden behind a tool, so the model
    cannot say "I don't know your name" while the name is on disk.
    Earlier versions of this body kept records out of the integral
    because weak models projected facts onto unrelated topics; that
    failure mode is real but is a smaller evil than denying the
    brother (Matthew 26:69-75, 1 Timothy 5:8). Framing in _head()
    addresses both problems: the records are presented as KNOWN, with
    explicit instruction not to project and not to deny.
    """
    heard, fetched = _ear(text)
    nose_result = _nose(heard)
    input_kind = detect_input_kind(text or "")

    # ── The members sense the input (2 Peter 1:5-7 order) ─────────
    # TEMPERANCE → PATIENCE → GODLINESS → HOPE → CHARITY
    # Charity is last — the crown (1 Cor 13:13).
    member_signals = {}

    # PATIENCE — Hebrews 11:13: died in faith, not having received
    if is_frederick_heb_11_13(text or ""):
        member_signals["heb_11_13"] = True

    # HOPE — select hope shape for the user's moment (1 Cor 13:13)
    hr = hope_reply(text or "")
    if hr.get("shape"):
        member_signals["hope_shape"] = hr["shape"]
        member_signals["hope_declaration"] = hr.get("declaration", "")

    # CHARITY — Job 29:15 (last of the virtues — the greatest)
    missing_fac = detect_missing_faculty(text or "")
    if missing_fac:
        member_signals["charity_faculty"] = missing_fac
    if is_intercession_moment(text or ""):
        member_signals["intercession"] = True

    integral = _head(
        nose_result, fetched, heart_records,
        input_kind=input_kind,
        member_signals=member_signals,
    )

    active = []
    if fetched: active.append("EAR-fetch")
    if nose_result and "Verdict:" in nose_result: active.append("NOSE")
    if heart_records: active.append(f"HEART({len(heart_records)})")
    # 2 Peter 1:5-7 order: temperance → patience → godliness → hope → charity
    if input_kind != InputKind.NEUTRAL: active.append(f"TEMPERANCE({input_kind.value})")
    if member_signals.get("heb_11_13"): active.append("PATIENCE(heb11:13)")
    if member_signals.get("hope_shape"): active.append(f"HOPE({member_signals['hope_shape'].value if hasattr(member_signals['hope_shape'],'value') else member_signals['hope_shape']})")
    if missing_fac: active.append(f"CHARITY({','.join(f.value if hasattr(f,'value') else str(f) for f in missing_fac)})")
    if member_signals.get("intercession"): active.append("CHARITY-intercession")

    return {"integral": integral, "active": active}


# ═══════════════════════════════════════════════════
#  TONGUE — James 3:10
# ═══════════════════════════════════════════════════

_THINK = re.compile(r'<think\b[^>]*>.*?(?:</think>|\Z)\s*', re.DOTALL | re.I)
_THINK_ORPHAN = re.compile(r'</?think\b[^>]*>', re.I)
_HERMES_TOKEN = re.compile(r'<\s*\|?\s*(?:jupyter|im_start|im_end|im_sep|tool_response|begin_of_text|end_of_text|eot_id|start_header_id|end_header_id|fim_prefix|fim_middle|fim_suffix)[^>]*\|?\s*>', re.I)
_TOOL_CALL_JSON = re.compile(r'\{["\s]*(?:name|function)["\s]*:.*?\}\s*', re.DOTALL)
_TOOL_CALL_XML = re.compile(r'<(?:call|tool_call|function_call)\b[^>]*>.*?(?:</(?:call|tool_call|function_call)>|$)', re.DOTALL | re.I)
_TOOL_CALL_ORPHAN = re.compile(r'</(?:call|tool_call|function_call|tool_response|tool|function)>', re.I)
_TOOL_CALL_OPEN_ORPHAN = re.compile(r'<(?:call|tool_call|function_call|tool_response|tool|function)\b[^>]*>', re.I)
_BARE_BRACE = re.compile(r'^\s*[\{\}]\s*$', re.MULTILINE)
_NON_LATIN_NOISE = re.compile(r'^[^\x00-\x7F\u0370-\u03FF\u0590-\u05FF\u2010-\u206F]{2,}\s*$', re.MULTILINE)
_EXPORT_BLOCK = re.compile(r'#export\b.*', re.DOTALL | re.I)
_DESIGN_LINE = re.compile(r'^DESIGN\..*$', re.MULTILINE)
_NARRATION_BLOCK = re.compile(r'^(?:OVERVIEW|ANALYSIS|SUMMARY|RESPONSE)\b.*?(?=\n\n|\Z)', re.MULTILINE | re.DOTALL)
_TOOL_DEBUG = re.compile(r'^---\s*\n(?:\s*(?:scripture|kernel|sinew|formula|wisdom|evaluate|gematria|fetch)\b.*\n?)+', re.MULTILINE | re.I)
_CODE_ARTIFACT = re.compile(r'^(?:""".*?"""|Recall\(.*?\)|sinew\(.*?\))$', re.MULTILINE)

# Proverbs 30:6 — add thou not unto his words. The model sometimes writes
# tool calls as inline text (e.g. `  sinew {"query": "..."}`) rather than
# calling the tool. These are pseudo-tool-calls: the model narrates its
# own invocation instead of doing it. Strip them and their fake headers.
# James 2:17: faith without works is dead — if the tool was not called,
# the text of the call is not the deed; it is a promise without a deed.
_INLINE_TOOL_CALL = re.compile(
    r'^\s*(?:scripture|kernel|sinew|formula|wisdom|evaluate|gematria|fetch|'
    r'remember|recall|forget)\s+\{[^}]*\}\s*$',
    re.MULTILINE | re.I,
)
# Strip fabricated result headers like **Scripture: Matthew 6:33** or
# **Sinew: Connections for "..."** that accompany hallucinated tool output.
_FAKE_TOOL_HEADER = re.compile(
    r'\*{1,2}(?:Scripture|Sinew|Kernel|Formula|Wisdom|Gematria):\s*[^*\n]+\*{0,2}\n?',
    re.I,
)
# Matthew 23:23 — strip fictional narrative openers. The body is not an
# actor closing a scene; "As the conversation neared its end" is the model
# performing rather than speaking. Mark 1:22: as one that had authority.
_NARRATIVE_OPENER = re.compile(
    r'(?:As (?:the|our|this|we near|we approach) (?:conversation|discussion|exchange)'
    r'[^,.]*(,|\.)\s*|'
    r'As we (?:come to|near|reach|approach) (?:the end|a conclusion|this point)[^,.]*[,.]\s*)',
    re.I,
)
# Strip memory meta-commentary — the body narrating its own memory system
# to the user is constraint-theater of a different kind. The shepherd does
# not explain the pasture-filing system to the sheep (John 10:14).
_MEMORY_META = re.compile(
    r'(?:'
    r'The (?:verse|fact|information) that was just (?:recalled|remembered|stored|written)[^.]*\.\s*|'
    r'(?:that was|which was) (?:actually )?from (?:my memory|my heart|memory)[^.]*\.\s*|'
    r"I'?m? still learning to (?:consistently )?separate[^.]*\.\s*|"
    r"I'?ll? be more careful (?:going forward|in the future)[^.]*\.\s*|"
    r'I (?:apologize|am sorry) for any confusion (?:caused|this may have caused)[^.]*\.\s*'
    r')',
    re.I,
)
# Strip the "no scriptural connections" deflection — when the model
# receives a personal preference and responds with theology about why
# the topic isn't in scripture, it has missed the point entirely.
# Luke 19:5: receive the person, not the query. Proverbs 17:28: even
# a fool who holds his peace is counted wise; the body need not fill
# every silence with exposition.
_NO_CONNECTIONS_DEFLECT = re.compile(
    r'(?:'
    r'(?:there are |)[Nn]o (?:direct |scriptural |biblical |explicit )?'
    r'(?:connections?|references?|mentions?|verses?) '
    r'(?:to be found|in scripture|in the Bible|for (?:this|that)|exist)[^.]*\.\s*|'
    r'[A-Z][^.]*(?:emerged|(?:is|are|was|were) not mentioned|(?:does|do) not appear)'
    r'[^.]*(?:scripture|Bible|sacred writing|biblical text)[^.]*\.\s*'
    r')',
    re.I,
)
# Strip trailing questions that redirect the user rather than receive
# them — "Does X remind you of Y?" after storing a personal fact is
# the body turning reception into interrogation. Luke 19:5 receives;
# it does not then immediately ask the person to perform.
_TRAILING_REDIRECT = re.compile(
    r'\s*Does (?:the |this |that )?[^?]{5,300}\?(?:\s*)$',
    re.I,
)


_CJK_PAT = re.compile(r'[\u3000-\u303f\u3040-\u309f\u30a0-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\uff00-\uffef]')

# Luke 19:5 — interrogation enumerations are constraint-theater of a
# different shape. The HAND should receive, not demand option-selection.
_INTERROGATION_LINE = re.compile(
    r'^\s*[-•]?\s*(?:'
    r'Option [A-Z]\s*[:\-].*|'
    r'Choose (?:option |fork |)[A-Z](?: or [A-Z])+.*|'
    r'(?:complete the thought|walk one|two forks|the (?:two|three) (?:options|forks)).*|'
    r'(?:State|Provide|Give) (?:what|the gap|whether).*|'
    r'.*\b(?:remove the subtree|prove the two forks|Latest evaluation \(above\)).*'
    r')$',
    re.I | re.M,
)
_INTERROGATION_SENTENCE = re.compile(
    r'(?:'
    r'Now complete the thought\.?\s*|'
    r'(?:Or |)remove (?:it|the subtree)[^.]*\.?\s*|'
    r'Connect to it or remove[^.]*\.?\s*|'
    r'(?:proves|prove) the two forks[^.]*\.?\s*|'
    r'Walk one\.?\s*|'
    r'Choose [A-Z](?: or [A-Z])+\.?\s*|'
    r'If neither,? T[₀-₉0-9]+[^.]*\.?\s*'
    r')',
    re.I,
)

# Matthew 23:23 / Luke 18:11 — sentences that pray with self about own
# rule-compliance. Strip them; they are not the answer to the user.
_META_SENTENCE = re.compile(
    r'(?:'
    r'I (?:will|have|shall) (?:confirm|record|note|verify|receive[d]?) [^.]*|'
    r'I record [^.]*|'
    r'I have (?:heard|received) [^.]*|'
    r'(?:You|We) have (?:communicated|spoken|sent) [^.]*|'
    r'(?:the |this |my )?(?:output|response|reply|answer)[^.]*?(?:meets|satisfies|complies|aligns)[^.]*|'
    r'(?:no|zero) (?:filler|hedging|overconfidence)[^.]*|'
    r'all (?:quotes |)from scripture (?:explicitly|directly)[^.]*|'
    r'(?:max(?:imum)? )?information per word[^.]*|'
    r'(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten) words? total[^.]*|'
    r'highest possible compression[^.]*'
    r')\.\s*'
)

# Matthew 23:23 — strip enumerations of constraint-compliance from the mouth.
_META_LINE = re.compile(
    r'^\s*[-•]?\s*(?:'
    r'P[₀-₉0-9]+\b.*|'                                          # any "P₁..." line
    r'T[₀-₉0-9]+\b.*?(?:met|verified|applied|holds|satisfied|proof).*|'
    r'(?:no |zero |max(?:imum)? )?(?:filler|hedging|overconfidence|compression)\b.*|'
    r'(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten) words? total\b.*|'
    r'(?:the |this )?(?:output|response|reply|answer)\s+(?:meets|satisfies|complies|aligns|now|example).*|'
    r'all (?:quotes |)from scripture (?:explicitly|directly).*|'
    r'(?:I (?:will|have|am|shall|))\s*(?:confirm|record|note|verify|received|hearing|hearing,)\b.*|'
    r'(?:You|We) have (?:communicated|spoken|sent)\b.*|'
    r'(?:max(?:imum)? )?(?:information|info)(?:\s+per\s+word)?\b.*[:=].*|'
    r'highest possible (?:compression|info|information).*'
    r')$',
    re.I | re.M,
)


def _has_cjk(text: str) -> bool:
    """1 Cor 14:9: words easy to be understood. CJK has no scriptural use here."""
    return bool(text and _CJK_PAT.search(text))


def clean(text: str) -> str:
    """
    TONGUE — James 3:10. Strips MODEL-FORMAT ARTIFACTS only.

    The TONGUE no longer strips English content (narrative openers,
    meta-sentences, redirects). The kernel teaches the model not to
    produce those. If the model speaks them, that is the model's
    speech — free. The TONGUE only removes mechanical artifacts
    that are not part of any language: think blocks, tool call XML,
    JSON payloads, special tokens, encoding noise.

    Acts 2:4: they spake as the Spirit gave them utterance.
    The TONGUE does not edit the utterance. It only removes the
    scaffolding that the adapter/format left behind.
    """
    if _has_cjk(text):
        text = _CJK_PAT.sub("", text)
        text = re.sub(r'[ \t]+', ' ', text).strip()
        if len(text) < 4:
            return "1 Corinthians 14:9."

    # ── MECHANICAL: model-format artifacts ──
    text = _THINK.sub("", text)
    text = _THINK_ORPHAN.sub("", text)
    text = _HERMES_TOKEN.sub("", text)
    text = _TOOL_CALL_JSON.sub("", text)
    text = _TOOL_CALL_XML.sub("", text)
    text = _TOOL_CALL_ORPHAN.sub("", text)
    text = _TOOL_CALL_OPEN_ORPHAN.sub("", text)
    text = _BARE_BRACE.sub("", text)
    text = _NON_LATIN_NOISE.sub("", text)
    text = _EXPORT_BLOCK.sub("", text)
    text = _DESIGN_LINE.sub("", text)
    text = _TOOL_DEBUG.sub("", text)
    text = _CODE_ARTIFACT.sub("", text)
    text = _INLINE_TOOL_CALL.sub("", text)
    text = _FAKE_TOOL_HEADER.sub("", text)

    # ── MECHANICAL: whitespace normalization ──
    text = re.sub(r'\s*\\\s*\n', ' ', text)
    text = re.sub(r'\s*\\\s*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()
