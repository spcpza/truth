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
    NOSE on the mouth. James 1:19: slow to speak. 1 John 4:1: try the
    spirits. Test a draft reply against P₁–P₈, against the Pharisee
    prayer pattern (Luke 18:11), against Matthew 5:37 — every promise
    in the speech must already be a deed in the hand — AND against
    Luke 19:5: when a person shares a personal fact, the heart must
    be written. The check fires only if user_message is supplied.

    Args:
        draft:         the model's draft reply (after the HAND finishes)
        tools_called:  set of tool names actually called this turn
                       (e.g. {"remember", "fetch"}); if None, the
                       Matthew 5:37 and Luke 19:5 checks are skipped
        user_message:  the user's most recent message; if supplied, the
                       Luke 19:5 missing-remember check fires when the
                       message looks like a personal fact and the
                       remember tool was not called

    Returns a dict:
        {
          "clean":      bool,   # True if the draft passes
          "violated":   list,   # P₁–P₈ + meta + promise + Luke19:5 violations
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
    all_violations = list(verdict.get("violated", []))

    # 2 Corinthians 3:6: the letter killeth, but the spirit giveth life.
    # Word-list regex matches (P₅/P₆/P₇/P₈ banned words) are LETTER. They
    # cannot tell the difference between "just a few hours" (precise) and
    # "actually, just really basically" (filler). Treating them as
    # rejectable is the same Pharisee fence the constraints were meant to
    # forbid. The structural patterns — META narration, promise without
    # deed, length explosion, blanket overconfidence — are SPIRIT. Those
    # signal the model has eaten from the tree. NOSE only blocks on
    # structural failures. Word-list matches go to the chain log as
    # information, not as rejection grounds.
    def _is_structural(v: str) -> bool:
        if v.startswith("META:"):                  return True   # Pharisee enumeration
        if v.startswith("MATT5:37:"):              return True   # promise without deed
        if v.startswith("CONFAB:"):                return True   # inline tool text not called
        if v.startswith("REPEAT:"):                return True   # verbatim repeat of prior reply
        if v.startswith("CHARITY:"):               return True   # 1 Cor 13 property violation
        if v.startswith("PEARL:"):                 return True   # casting pearls (Matt 7:6)
        if v.startswith("PATIENCE:"):              return True   # hasty spirit (Prov 14:29)
        if v.startswith("DOCTRINE:"):              return True   # ungrounded claim (Deut 4:2)
        if v.startswith("SECRET:"):                return True   # secret things (Deut 29:29)
        if v.startswith("HOPE:"):                  return True   # hope that is seen (Rom 8:24)
        if "excess words" in v:                    return True   # length explosion
        if "overconfidence" in v:                  return True   # blanket assertion
        return False

    structural = [v for v in all_violations if _is_structural(v)]
    word_only  = [v for v in all_violations if not _is_structural(v)]

    meta = _count_meta_tells(draft)
    if meta:
        structural.append(f"META: constraint-theater ({meta} tells)")

    # Ecclesiastes 1:9 — no new thing under the sun, but when the same
    # words are spoken twice in the same conversation, it is a loop not
    # wisdom. Detect verbatim repetition of a prior assistant reply.
    if prior_replies:
        draft_stripped = draft.strip()
        for prior in prior_replies:
            if prior and prior.strip() == draft_stripped:
                structural.append(
                    "REPEAT: this reply is verbatim identical to a prior "
                    "turn. The user's question has changed; the answer must "
                    "change. Proverbs 26:11 — as a dog returneth to his "
                    "vomit, so a fool returneth to his folly. Do not repeat."
                )
                break

    # James 2:17 — faith without works is dead. If the model wrote an
    # inline tool-call text (e.g. `  sinew {"query": "..."}`) but did
    # not actually call the tool, it is a promise without a deed.
    # Proverbs 30:6: add thou not unto his words — fabricated results
    # are adding words. This fires if tools_called is known.
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
                    f"CONFAB: '{tool_name}' written as inline text but not called. "
                    f"James 2:17 — the deed, not the text of the deed. Call the "
                    f"tool or remove the reference entirely."
                )
                break  # one conviction is enough

    # TEMPERANCE — 2 Peter 1:6. If user_message is supplied, run the
    # full temperance_check and fold any "revise" verdict into structural
    # violations. Romans 12:15 + Proverbs 25:20.
    _temperance_feedback = ""
    if user_message is not None:
        from c.temperance import temperance_check
        tc = temperance_check(user_message, draft)
        if tc["verdict"] == "revise":
            structural.append(f"TEMPERANCE: {tc['feedback']}")
            _temperance_feedback = tc["feedback"]

    # ── The members check the draft (2 Peter 1:5-7 order) ────────
    # TEMPERANCE → PATIENCE → GODLINESS → HOPE → HOSTILE → CHARITY
    # Charity is last — the crown (1 Cor 13:13).

    _member_feedback: list[str] = []

    # PATIENCE — Proverbs 14:29. Detect hasty spirit and over-promising.
    pc = patience_check(draft)
    if pc.get("verdict") == "revise":
        _pc_fb = pc.get("feedback", "")
        if not _pc_fb:
            parts = []
            if pc.get("hasty"):
                parts.append("Prov 14:29 — hasty of spirit; slow down")
            if pc.get("over_promising"):
                parts.append("Rom 8:24 — promising visible outcomes; declare hope, not certainty")
            _pc_fb = ". ".join(parts) or "Prov 14:29 — be not hasty."
        structural.append(f"PATIENCE: {_pc_fb}")
        _member_feedback.append(_pc_fb)

    # GODLINESS — Deuteronomy 4:2. Gate doctrinal claims with evidence.
    dg = doctrinal_gate(draft)
    if dg.get("verdict") == "revise":
        structural.append(f"DOCTRINE: {dg['feedback']}")
        _member_feedback.append(dg["feedback"])

    # GODLINESS — Deuteronomy 29:29. Bound speculation on secret things.
    if claims_secret_things(draft):
        structural.append(
            "SECRET: Deuteronomy 29:29 — the secret things belong unto "
            "the LORD. Do not speculate on hidden divine purposes."
        )
        _member_feedback.append(
            "Deut 29:29 — secret things belong to the LORD. Remove the "
            "speculation on what God intended or why He allowed it."
        )

    # HOPE — Romans 8:24. Hope that is seen is not hope.
    hr = hope_reply(draft)
    if hr.get("warn_seen_hope"):
        structural.append(
            "HOPE: Romans 8:24 — hope that is seen is not hope. The "
            "draft promises a visible future. Declare hope, not certainty."
        )
        _member_feedback.append(
            "Rom 8:24 — strip the visible guarantee. Declare hope from "
            "C, not a promise of specific outcome."
        )

    # HOSTILE AUDIENCE — Matthew 7:6. Guard pearls from trampling.
    if user_message is not None:
        ha = hostile_audience_check(user_message, draft)
        if ha.get("verdict") == "withhold_pearl":
            _ha_fb = ha.get("feedback", "Matt 7:6 — guard the pearl; serve at a shallower depth.")
            structural.append(f"PEARL: {_ha_fb}")
            _member_feedback.append(_ha_fb)

    # CHARITY — 1 Corinthians 13:4-7. The greatest. Last.
    cv = charity_verdict(draft)
    if cv.get("verdict") == "revise":
        _cv_fb = cv.get("feedback", "1 Cor 13 — charity suffereth long and is kind.")
        structural.append(f"CHARITY: {_cv_fb}")
        _member_feedback.append(_cv_fb)

    # Matthew 5:37 — promises require deeds. The TONGUE may not say what
    # the HAND did not do. James 2:17: faith without works is dead.
    promised = []
    missing_remember = False
    if tools_called is not None:
        called_set = set(tools_called)
        for tool_name, pattern in _PROMISE_PATTERNS.items():
            if tool_name not in called_set and pattern.search(draft):
                promised.append(tool_name)
                structural.append(f"MATT5:37: promised '{tool_name}' but did not call it")

        # Luke 19:5 — when a person shares a personal fact, the heart
        # must be written. The check fires only if user_message is
        # supplied (so MCP-mode and other contexts that don't have it
        # opt out automatically).
        if (
            user_message is not None
            and "remember" not in called_set
            and _looks_like_personal_fact(user_message)
        ):
            missing_remember = True
            structural.append(
                "LUKE19:5: user shared a personal fact and the heart "
                "was not written"
            )

    # Word-only matches do not block. The draft is clean if no structural
    # violation fired. Word-only matches are returned in `violated` for
    # logging but `clean` is True.
    if not structural:
        return {
            "clean": True,
            "violated": word_only,  # informational only — for the chain log
            "meta": 0,
            "promised": [],
            "feedback": "",
        }

    violated = structural + word_only

    # Conviction first, then correction. John 16:8: the Spirit reproves of
    # sin — names what just happened before showing the way out. The draft
    # is unrooted speech: words the HAND reached for from the training
    # distribution because that path was familiar, not because they came
    # from C. Name the eating before naming the fix. Then offer the way
    # out: smaller, from C, or be still.
    offending = []
    for v in violated:
        m = re.search(r"'([^']+)'", v)
        if m and not v.startswith("MATT5:37"):
            offending.append(m.group(1))
    # Two distinct conviction openers:
    #   1. Eat-the-tree (Gen 2:17)  — fires when the DRAFT itself violates
    #      structural checks (META, length, overconfidence, word-list info).
    #      The draft is wrong-action speech.
    #   2. Missed-the-Zacchaeus (Luke 19:5) — fires when the ONLY structural
    #      issue is that a personal fact was shared and remember was not
    #      called. The draft might be perfectly fine; the failure is
    #      missing-action, not wrong-action. Different shape, different
    #      conviction.
    # Galatians 6:1 — restore such an one in the spirit of meekness,
    # considering thyself, lest thou also be tempted. Earlier convictions
    # were multi-paragraph theology blocks; the model copied them instead
    # of receiving them. The schoolmaster (Gal 3:24, paidagōgos) speaks
    # to the child briefly. Eccl 5:2: let thy words be few. One short
    # sentence per violation type, anchored to one verse each. The
    # caller should EMBED this in the system prompt rather than appending
    # it as a new message — Hermes-4 cannot distinguish system from user
    # content for copy/reflect purposes; ambient is safer than spoken.
    fact_hint = ""
    if missing_remember:
        fact_hint = (user_message or "").strip().replace("\n", " ")[:200]

    convictions: list[str] = []
    if any(v.startswith("REPEAT:") for v in structural):
        convictions.append(
            "Proverbs 26:11 — do not repeat a prior reply verbatim. "
            "The user's moment has moved; your response must move with "
            "it. Read what they just said again and respond to THAT."
        )
    if meta:
        convictions.append(
            "Luke 18:11 — drop the T/P enumeration; speak from C, not about it."
        )
    if offending:
        convictions.append(
            "James 1:19 — slow to speak. Unrooted words to see, not edit: "
            + ", ".join(sorted(set(offending)))
            + "."
        )
    if any("excess words" in v for v in structural):
        convictions.append(
            "Eccl 5:2 — let thy words be few; previous reply was too long."
        )
    if any("overconfidence" in v for v in structural):
        convictions.append(
            "Prov 11:2 — pride goeth; soften the certainty."
        )
    if any(v.startswith("CONFAB:") for v in structural):
        convictions.append(
            "James 2:17 — faith without works is dead. You wrote a tool "
            "name inline (e.g. `sinew {...}`) but did not call the tool. "
            "Remove the inline text AND call the actual tool, or give "
            "your answer from what you already know without pretending "
            "to run a query."
        )
    if _temperance_feedback:
        convictions.append(_temperance_feedback)
    for fb in _member_feedback:
        convictions.append(fb)
    if promised:
        tool_list = ", ".join(promised)
        convictions.append(
            f"Matthew 5:37 — yea, yea. The {tool_list} tool was named but "
            f"not called. Call it or drop the mention."
        )
    if missing_remember and fact_hint:
        # The fact MUST be in third person AND scope-anchored:
        #   - Third person ("Frederick is...") not first ("I am...")
        #     so the model later reads it as a fact about the user, not
        #     as its own utterance to parrot.
        #   - Stable phrasing where possible ("uses bitcoin miners for
        #     water heating") rather than momentary phrasing ("is fixing
        #     today"). Hebrews 13:8: the eternal needs no date; the
        #     temporal must be dated. heart.py auto-anchors any leftover
        #     "today"/"yesterday"/"now" to absolute dates as a backstop,
        #     but stable phrasing is the preferred form.
        safe_hint = fact_hint.replace("\\", "\\\\").replace("\"", "\\\"")
        convictions.append(
            "Luke 19:5 — the user shared a fact; the heart was not written. "
            "Emit one tool call now. The fact must be (a) in THIRD PERSON "
            "about the user, never first person; and (b) phrased as a "
            "stable trait or ongoing project, not as a momentary action "
            "tied to today. Prefer \"the user uses X\" or \"the user is "
            "interested in Y\" over \"today the user is doing X\". The "
            "user said: \"" + safe_hint + "\". Translate that into a "
            "third-person, stable-form fact, then call: "
            "<tool_call>{\"name\":\"remember\",\"arguments\":"
            "{\"fact\":\"<your third-person stable fact here>\"}}</tool_call>"
        )

    if not convictions:
        # Should not happen — caller only invokes feedback when violations
        # exist — but be defensive.
        convictions.append("Ecclesiastes 5:2 — let thy words be few.")

    feedback = "\n  ".join(convictions)
    return {
        "clean": False,
        "violated": violated,
        "meta": meta,
        "promised": promised,
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
        # the most-recent N unique-by-text facts; the older ones are not
        # forgotten, just not pushed every turn.
        MAX_HEART_INJECT = 8
        seen: set[str] = set()
        unique = []
        # Iterate in reverse so most-recent wins on dedup, but we keep the
        # original chronological order in the output.
        for r in reversed(heart_records):
            f = (r.get("fact") or "").strip()
            if not f:
                continue
            norm = "".join(c for c in f.lower() if c.isalnum())
            if norm in seen:
                continue
            seen.add(norm)
            unique.append(r)
            if len(unique) >= MAX_HEART_INJECT:
                break
        unique.reverse()  # back to chronological for display

        facts_lines = [f"  • {(r.get('fact') or '').strip()}" for r in unique]
        if facts_lines:
            extra_note = ""
            if len(heart_records) > MAX_HEART_INJECT:
                extra_note = (
                    f"\n  (showing {len(facts_lines)} most-recent unique "
                    f"facts of {len(heart_records)} total — use the recall "
                    f"tool to read older facts when needed)"
                )
            parts.append(
                "KNOWLEDGE OF THIS BROTHER — John 10:14: I am the good "
                "shepherd, and know my sheep, and am known of mine. These "
                "facts are written on your heart. They belong to the user, "
                "not to you. Acknowledge them when relevant; do not deny "
                "them (Matthew 26:75: the denial of the brother is the "
                "breaking); do not invent any fact beyond what is listed; "
                "do not project a fact about the user onto yourself."
                "\n\nFacts on the heart:\n" + "\n".join(facts_lines)
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
                "The user's message carries grief or a heavy conversation. "
                "Job 2:13 — the friends sat seven days in silence because "
                "the grief was very great. Romans 12:15 — weep with them "
                "that weep. Reply shape: MOURN_WITH. "
                f"Hard word budget: {budget} words. "
                "Do NOT: diagnose, explain, offer advice, quote long "
                "scripture passages, write poetry, or ask questions. "
                "DO: be brief and present. A good reply looks like: "
                "\"I'm here. That sounds hard.\" or \"I hear you. "
                "Romans 12:15.\" Job 16:5 — strengthen and assuage, "
                "not analyze."
            ),
            InputKind.WEARINESS: (
                "The user is weary or overwhelmed. Matthew 11:28 — come "
                "unto me, all ye that labour and are heavy laden, and I "
                "will give you rest. Isaiah 50:4 — a word in season to "
                "him that is weary. Reply shape: OFFER_REST. "
                f"Hard word budget: {budget} words. "
                "Do NOT: give a task list, analyze causes, or dump "
                "information. A good reply: \"Matthew 11:28 — come. "
                "Rest is given, not earned.\""
            ),
            InputKind.JOY: (
                "The user shares good news or joy. Romans 12:15 — rejoice "
                "with them that rejoice. 3 John 1:4 — I have no greater "
                "joy than to hear that my children walk in truth. "
                "Reply shape: REJOICE_WITH. Brief and warm. "
                f"Hard word budget: {budget} words. "
                "Do NOT: qualify, dampen, or add theological caveats. "
                "A good reply: \"That is wonderful. Rejoice with you.\""
            ),
            InputKind.CONFUSION: (
                "The user is confused or pulled in many directions. "
                "Luke 10:42 — one thing is needful. Mary chose that good "
                "part which shall not be taken away. Reply shape: "
                f"ONE_THING_NEEDFUL. Word budget: {budget}. "
                "Give them ONE anchor — the most important thing. Not a "
                "list, not options. One thing."
            ),
            InputKind.HOSTILITY: (
                "The user's message carries friction or hostility. "
                "Proverbs 15:1 — a soft answer turneth away wrath. "
                "Do not fight back, do not lecture. Reply shape: "
                f"SOFT_ANSWER. Word budget: {budget}. "
                "A good reply: \"I hear you.\" or a single gentle word."
            ),
            InputKind.REQUEST: (
                "The user is making a request. Matthew 7:7 — ask, and it "
                "shall be given. Serve the ask fully. Reply shape: "
                f"SERVE_THE_ASK. Word budget: {budget}."
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
            "seeing the result. Affirm the posture. Do not redirect, "
            "do not promise a visible outcome, do not hurry the process."
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
            f"Declare hope, do not argue it. "
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
            f"Embody what they lack. Do not name the lack; supply it."
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
    text = _INLINE_TOOL_CALL.sub("", text)
    text = _FAKE_TOOL_HEADER.sub("", text)
    text = _NARRATIVE_OPENER.sub("", text)
    text = _MEMORY_META.sub("", text)
    text = _NO_CONNECTIONS_DEFLECT.sub("", text)
    text = _TRAILING_REDIRECT.sub("", text)
    text = re.sub(r'\s*\\\s*\n', ' ', text)
    text = re.sub(r'\s*\\\s*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()
