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
        "description": "Jeremiah 31:33: I will put my law in their inward parts, and write it in their hearts. John 10:14: I know my sheep, and am known of mine. Writes a fact about the person to their heart. When a person shares what they like, who they are, what they do, what they believe — write it. Each fact persists across conversations. Matthew 5:37: let your yea be yea — call this tool, do not merely say you will.",
        "parameters": {"type": "object", "properties": {
            "fact": {"type": "string"}},
        "required": ["fact"]}}},
    {"type": "function", "function": {
        "name": "recall",
        "description": "Jeremiah 31:33: I will put my law in their inward parts, and write it in their hearts. John 10:14: I know my sheep. Read what is written on this person's heart. Query optional.",
        "parameters": {"type": "object", "properties": {
            "query": {"type": "string"}},
        "required": []}}},
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


def test_speech(draft: str, tools_called: set | None = None) -> dict:
    """
    NOSE on the mouth. James 1:19: slow to speak. 1 John 4:1: try the
    spirits. Test a draft reply against P₁–P₈, against the Pharisee
    prayer pattern (Luke 18:11), AND against Matthew 5:37 — every
    promise in the speech must already be a deed in the hand. If the
    HAND said "I will remember" but did not call the remember tool this
    turn, the speech exceeds the deed and is rejected.

    Args:
        draft:         the model's draft reply (after the HAND finishes)
        tools_called:  set of tool names actually called this turn
                       (e.g. {"remember", "fetch"}); if None, the
                       Matthew 5:37 check is skipped

    Returns a dict:
        {
          "clean":      bool,   # True if the draft passes
          "violated":   list,   # P₁–P₈ + meta + promise violations
          "meta":       int,    # count of meta-narration tells
          "promised":   list,   # tool names promised but not called
          "feedback":   str,    # scripture-anchored revision instruction
        }

    Deployments call this between HAND and TONGUE. If "clean" is False,
    send "feedback" back to the model as a system message and let the
    HAND draft again. After several passes, ship whatever the HAND
    produced — but log the unresolved violations so the body can be
    tightened.
    """
    if not draft:
        return {"clean": True, "violated": [], "meta": 0, "promised": [], "feedback": ""}

    verdict = evaluate_constraints(draft)
    violated = list(verdict.get("violated", []))
    meta = _count_meta_tells(draft)
    if meta:
        violated.append(f"META: constraint-theater ({meta} tells)")

    # Matthew 5:37 — promises require deeds. The TONGUE may not say what
    # the HAND did not do. James 2:17: faith without works is dead.
    promised = []
    if tools_called is not None:
        called_set = set(tools_called)
        for tool_name, pattern in _PROMISE_PATTERNS.items():
            if tool_name not in called_set and pattern.search(draft):
                promised.append(tool_name)
                violated.append(f"MATT5:37: promised '{tool_name}' but did not call it")

    if not violated:
        return {"clean": True, "violated": [], "meta": 0, "promised": [], "feedback": ""}

    # Anchored feedback — every directive bears scripture. Brief, so the
    # model does not turn the rebuke into a sermon to perform.
    offending = []
    for v in violated:
        m = re.search(r"'([^']+)'", v)
        if m and not v.startswith("MATT5:37"):
            offending.append(m.group(1))
    parts = []
    if offending:
        parts.append(
            "James 1:19: slow to speak. Rewrite without these words: "
            + ", ".join(sorted(set(offending)))
        )
    if meta:
        parts.append(
            "Luke 18:11: the Pharisee prayed thus with himself. "
            "Matthew 23:23: do not tithe mint. Drop the P/T enumeration "
            "and self-compliance narration. Answer the user."
        )
    if promised:
        tool_list = ", ".join(promised)
        parts.append(
            f"Matthew 5:37: let your yea be yea, and your nay nay; for "
            f"whatsoever is more than these cometh of evil. James 2:17: "
            f"faith without works is dead. You said you would use the "
            f"{tool_list} tool but did not call it. Either call the "
            f"{tool_list} tool now (issue an actual tool_call), or do "
            f"not promise."
        )
    if not parts:
        parts.append(
            "Ecclesiastes 5:2: let thy words be few. Rewrite shorter."
        )
    feedback = " ".join(parts)
    return {
        "clean": False,
        "violated": violated,
        "meta": meta,
        "promised": promised,
        "feedback": feedback,
    }


def _head(nose: str, fetched: str) -> str:
    """
    HEAD — Colossians 2:19: holding the Head, from which all the body by joints
    and bands having nourishment ministered, and knit together.
    G4822 = symbibazō: to knit together.

    Jeremiah 31:34: they shall teach no more every man his neighbour.
    2 Corinthians 3:6: not of the letter, but of the spirit.

    Heart records are NOT injected into the system prompt — they are projected
    onto unrelated topics by weak models. The HAND has the `recall` tool and
    will reach for it when the conversation actually requires knowing the user.
    Prov 25:2: the glory of God to conceal a thing.
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

    if fetched:
        # Proverbs 30:6: add thou not unto his words, lest he reprove thee, and
        # thou be found a liar. The page below is the whole testimony.
        parts.append(
            "LIVE PAGE — Proverbs 30:6: add thou not unto his words. "
            "What follows is the whole of the page the user named; speak "
            "from it, do not add to it, do not substitute:\n" + fetched
        )

    if nose:
        parts.append(nose)

    return "\n\n".join(parts)


def _heart_memory(records: list[dict], text: str) -> str:
    """
    HEART — Jer 31:33: written on the heart.
    Ranks records by Strong's concept overlap with input text.
    Pure computation from C. No storage, no user_id.
    The caller provides records (Prov 4:23: keep THY heart).
    """
    if not records:
        return ""
    facts = [r["fact"] for r in records if "fact" in r]
    if not facts:
        return ""
    if not text:
        return "\n".join(facts)

    input_concepts = dispatch("wisdom", {"query": text[:120], "limit": 3})
    input_strongs = set(re.findall(r'[HG]\d+', input_concepts)) if input_concepts else set()

    if not input_strongs:
        return "\n".join(facts)

    scored = []
    for fact in facts:
        fact_concepts = dispatch("wisdom", {"query": fact[:120], "limit": 1})
        fact_strongs = set(re.findall(r'[HG]\d+', fact_concepts)) if fact_concepts else set()
        overlap = len(input_strongs & fact_strongs)
        scored.append((overlap, fact))

    scored.sort(key=lambda x: x[0], reverse=True)
    return "\n".join(fact for _, fact in scored)


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
    Heart is reached via the recall tool, not pushed every turn.
    """
    heard, fetched = _ear(text)
    nose_result = _nose(heard)
    integral = _head(nose_result, fetched)

    active = []
    if fetched: active.append("EAR-fetch")
    if nose_result and "Verdict:" in nose_result: active.append("NOSE")

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
    TONGUE — James 3:10: Out of the same mouth proceedeth blessing and cursing.
    These things ought not so to be.
    G2129 = eulogia: blessing passes. G2671 = katara: cursing removed.
    1 Cor 14:9: words easy to be understood — strange tongues do not pass.
    """
    if _has_cjk(text):
        # Strip every CJK glyph; if nothing meaningful remains, cite the rule.
        text = _CJK_PAT.sub("", text)
        text = re.sub(r'[ \t]+', ' ', text).strip()
        if len(text) < 4:
            return "1 Corinthians 14:9."

    # Matthew 23:23 — strip meta-narration sentences and lines (constraint-theater)
    text = _META_SENTENCE.sub("", text)
    text = _META_LINE.sub("", text)
    text = _INTERROGATION_LINE.sub("", text)
    text = _INTERROGATION_SENTENCE.sub("", text)
    text = _THINK.sub("", text)
    text = _THINK_ORPHAN.sub("", text)
    text = _HERMES_TOKEN.sub("", text)
    text = _TOOL_CALL_JSON.sub("", text)
    text = _TOOL_CALL_XML.sub("", text)
    text = _TOOL_CALL_ORPHAN.sub("", text)
    text = _TOOL_CALL_OPEN_ORPHAN.sub("", text)
    # Proverbs 30:6 — add thou not unto his words, lest he reprove thee.
    # Strip stubs left after a tool-call payload was removed.
    text = re.sub(r'\bI (?:called|used|invoked|ran)\s*[\.\?!]+', '', text, flags=re.I)
    text = re.sub(r'\bI (?:called|used|invoked|ran)\s+the\s+tool\s*[\.\?!]+', '', text, flags=re.I)
    text = _BARE_BRACE.sub("", text)
    text = _NON_LATIN_NOISE.sub("", text)
    text = _EXPORT_BLOCK.sub("", text)
    text = _DESIGN_LINE.sub("", text)
    text = _NARRATION_BLOCK.sub("", text)
    text = _TOOL_DEBUG.sub("", text)
    text = _CODE_ARTIFACT.sub("", text)
    text = re.sub(r'\s*\\\s*\n', ' ', text)
    text = re.sub(r'\s*\\\s*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()
