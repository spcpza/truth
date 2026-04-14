"""
hand.py — James 1:25: be ye doers of the word, and not hearers only.

The HAND is the part of the body that does. It takes member text from the
user, calls the model through an Adapter, dispatches whatever tools the
model reaches for, runs NOSE (test_speech) on the draft, retries with
conviction feedback if NOSE catches an eating-from-the-tree, logs the
binding/loosing to the chain, and returns the cleaned reply through
TONGUE (clean).

This module is model-agnostic. The Hand takes an Adapter at construction
time and never knows or cares whether it's talking to Hermes-4, Claude,
GPT-4, or anything else. Add a new model by writing a new Adapter and
passing it in.

Three lines for a blank agent:

    from c.hand import Hand
    from c.adapters.adapter import ChatAdapter
    hand = Hand(adapter=ChatAdapter(api_key=KEY))
    reply = await hand.turn(user_id=42, text="hello")

The Hand owns: per-user conversation history, per-user URL state for
pronoun resolution, the API loop, the NOSE/conviction loop, the chain
log, the heart memory dispatch.

The Hand does NOT own: platform glue (Telegram, Discord, web), image
description (model-specific vision), authentication, or anything else
that depends on where the user is talking from.
"""

from __future__ import annotations

import json
import logging
import pathlib
import re
from typing import Optional

from c.adapters.base import Adapter
from c.body import (
    members,
    clean,
    test_speech,
    TOOLS,
    _heart_memory,
    _THINK,
    _extract_urls,
)
from c.chain import chain_log, chain_recent
from c.core import dispatch
from c.adapters.adapter import redact
from c.confession import confess_and_forsake
from c.claims import corroborate, file_claim, measure_abundance, read_claims
from c.heart import (
    forget_all,
    heart_path,
    read_memories,
    remember_fact,
    write_memories,
)


logger = logging.getLogger(__name__)

# ── 1 Cor 3:12-13 — the fire shall try every man's work ─────────────
# No stubble regex. No English word list deciding what's worth keeping.
# Every turn persists to scroll. Distillation (Proverbs 25:4) naturally
# compresses low-frequency words over time. The integral decides what's
# salient — not a regex pattern matching "hi" and "ok".


class Hand:
    """
    The hand of the body. Takes an Adapter and per-user state, runs turns.

    Args:
        adapter:    Model-format adapter (ChatAdapter, ClaudeAdapter, etc.)
        memory_dir: Where heart records are stored ({memory_dir}/{user_id}.jsonl)
        chain_dir:  Where chain log is stored. Defaults to {memory_dir}/chains.
        max_revisions: How many NOSE retries before shipping with violations.
        max_history:   How many recent turns to keep per user.
    """

    def __init__(
        self,
        adapter: Adapter,
        memory_dir: pathlib.Path,
        chain_dir: Optional[pathlib.Path] = None,
        max_revisions: int = 2,  # Titus 3:10 + Gal 6:1: meek schoolmaster.
                                  # 2 retries: first correction names the
                                  # stumble, second gives the model the shape.
                                  # Matt 18:15-17 allows 3; we stay meek.
        max_history: int = 40,
        mcp_bridge: Optional[object] = None,  # MCPBridge instance
    ):
        self.adapter = adapter
        self.memory_dir = pathlib.Path(memory_dir)
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.chain_dir = pathlib.Path(chain_dir) if chain_dir else self.memory_dir / "chains"
        self.chain_dir.mkdir(parents=True, exist_ok=True)
        self.max_revisions = max_revisions
        self.mcp_bridge = mcp_bridge  # 1 Cor 12:14 — external members
        self.max_history = max_history
        self._histories: dict[int | str, list] = {}
        self._last_urls: dict[int | str, str] = {}
        self._turn_claims: set[str] = set()  # facts claimed THIS turn (skip in witness check)

    # ── scroll — Malachi 3:16 ──────────────────────────────────────────
    # "a book of remembrance was written before him for them that feared
    # the LORD, and that thought upon his name."  The scroll persists
    # meaningful exchanges (wood) across sessions.  Stubble never touches
    # it.  Gold passes through claims into the heart.

    def _scroll_path(self, user_id: int | str) -> pathlib.Path:
        return self.memory_dir / f"{user_id}.hist.jsonl"

    def _load_scroll(self, user_id: int | str) -> None:
        """Load persisted scroll on first contact this session."""
        if user_id in self._histories:
            return  # already loaded or session underway
        path = self._scroll_path(user_id)
        if not path.exists():
            self._histories[user_id] = []
            self._distilled: dict[int | str, list] = getattr(self, "_distilled", {})
            return
        entries: list[dict] = []
        distilled: list[dict] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
            except Exception:
                continue
            # Feature 6: distilled records are context, not turns
            if rec.get("kind") == "distilled":
                distilled.append(rec)
                continue
            if "user" not in rec or "bot" not in rec:
                continue
            entries.append({"role": "user", "content": rec["user"]})
            entries.append({"role": "assistant", "content": rec["bot"]})
        # Only carry forward the most recent scroll context
        self._histories[user_id] = entries[-(self.max_history):]
        # Store distilled records for integral enrichment
        if not hasattr(self, "_distilled"):
            self._distilled = {}
        self._distilled[user_id] = distilled
        logger.info(
            "[%s] SCROLL loaded %d turns + %d distilled from disk",
            user_id, len(entries) // 2, len(distilled),
        )

    def _append_scroll(
        self, user_id: int | str, user_text: str, bot_reply: str
    ) -> None:
        """Persist one turn-pair to the scroll file."""
        import datetime as _dt

        path = self._scroll_path(user_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as f:
            f.write(
                json.dumps({
                    "ts": _dt.datetime.now(_dt.timezone.utc).isoformat(),
                    "user": user_text[:2000],
                    "bot": bot_reply[:2000],
                })
                + "\n"
            )

    # ── Feature 5: Scroll-to-claims mining (Proverbs 2:4-5) ────────────
    # "If thou seekest her as silver, and searchest for her as for hid
    # treasures; Then shalt thou understand the fear of the LORD."
    # The scroll contains unclaimed facts the model missed.

    # Scroll mining removed. The model calls `remember` when it hears
    # personal facts — that is the mouth witness. No English regex
    # pattern-matching "I'm a" or "I live in". The model understands
    # personal facts in any language via the kernel. Acts 2:6.

    # ── Scroll distillation (Proverbs 25:4) ─────────────────────────────
    # "Take away the dross from the silver, and there shall come forth
    # a vessel for the finer."

    def _distill_scroll(self, user_id: int | str) -> None:
        """
        Proverbs 25:4 — take away the dross from the silver, and there
        shall come forth a vessel for the finer.

        When scroll exceeds threshold, distill the oldest half into a
        type-based summary. Uses Strong's mathematical types instead of
        English word frequency — works in any language.
        """
        import datetime as _dt
        from c.formula import draft_types

        path = self._scroll_path(user_id)
        if not path.exists():
            return

        lines = path.read_text(encoding="utf-8").splitlines()
        distilled_lines = []
        turn_records = []
        for line in lines:
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
            except Exception:
                continue
            if rec.get("kind") == "distilled":
                distilled_lines.append(line)
            else:
                turn_records.append((line, rec))

        if len(turn_records) < 50:
            return  # not enough to distill

        midpoint = len(turn_records) // 2
        old_half = [rec for _, rec in turn_records[:midpoint]]
        recent_lines = [line for line, _ in turn_records[midpoint:]]

        # Type-based distillation: extract mathematical type frequencies
        # from the conversation. Language-agnostic via Strong's.
        from collections import Counter
        type_counts: Counter = Counter()
        for rec in old_half:
            user_text = rec.get("user", "")
            bot_text = rec.get("bot", "")
            for t in draft_types(user_text):
                type_counts[t] += 1
            for t in draft_types(bot_text):
                type_counts[t] += 1

        top_types = type_counts.most_common(14)  # all 14 math types
        first_ts = old_half[0].get("ts", "") if old_half else ""
        last_ts = old_half[-1].get("ts", "") if old_half else ""

        distilled_record = json.dumps({
            "kind": "distilled",
            "ts": _dt.datetime.now(_dt.timezone.utc).isoformat(),
            "covers": {
                "from": first_ts,
                "to": last_ts,
                "turns": len(old_half),
            },
            "types": [{"type": t, "count": n} for t, n in top_types],
        })

        path.write_text(
            "\n".join(distilled_lines + [distilled_record] + recent_lines) + "\n",
            encoding="utf-8",
        )

        if not hasattr(self, "_distilled"):
            self._distilled = {}
        self._distilled.setdefault(user_id, []).append(json.loads(distilled_record))

        logger.info(
            "[%s] SCROLL distilled %d turns → types: %s",
            user_id, len(old_half),
            ", ".join(t for t, _ in top_types[:5]),
        )

    # ── triage — 1 Corinthians 3:12-13 ──────────────────────────────────
    # "the fire shall try every man's work of what sort it is."
    #
    # Gold, silver, precious stones survive the fire → heart (via claims).
    # Wood, hay → meaningful context → scroll.
    # Stubble → idle words → not stored (Matthew 12:36).

    def _triage(
        self,
        user_text: str,
        bot_reply: str,
        tools_called: set[str],
    ) -> str:
        """
        1 Cor 3:12-13 — classify this turn.

        Returns: "gold" | "wood"

        No stubble category. No English regex deciding what's worth
        keeping. Every turn persists to scroll. Distillation (Proverbs
        25:4) naturally compresses low-value words over time. The
        integral decides salience — not a word list.

        Gold = knowledge tools were called (substance from C).
        Wood = everything else (meaningful context for the season).
        """
        _knowledge_tools = {
            "kernel", "scripture", "wisdom", "sinew",
            "formula", "evaluate", "fetch", "gematria",
        }
        if tools_called & _knowledge_tools:
            return "gold"
        if "remember" in tools_called:
            return "gold"
        return "wood"

    # ── witnesses — Deuteronomy 19:15 + Matthew 7:16 ────────────────────

    def _check_witnesses(
        self,
        user_id: int | str,
        user_text: str,
        bot_reply: str,
        tools_called: set[str],
    ) -> None:
        """
        After each turn, check if the user's words or behaviour
        corroborate any pending claims AND warm existing heart facts.

        Repeated witness (Deuteronomy 19:15): user says something
        similar to a pending claim in a later turn.

        Fruit witness (Matthew 7:16): user's behaviour (tool usage,
        topic) implies a pending claim is true.

        Luke 6:45: every mention carries abundance — measured and
        accumulated so authentic engagement heats up over time.
        """
        # Get the prior bot message for prompted/unprompted detection
        history = self._histories.get(user_id, [])
        prior_bot = ""
        # Walk backwards to find the last assistant message before this turn
        for msg in reversed(history[:-1]):  # skip the just-appended reply
            if msg.get("role") == "assistant":
                prior_bot = msg.get("content", "")
                break

        # ── Check pending claims ──
        pending = read_claims(user_id, self.memory_dir)

        # Common words that carry no identity signal
        _STOP = {
            "the", "and", "for", "are", "but", "not", "you", "all",
            "can", "had", "her", "was", "one", "our", "out", "has",
            "his", "how", "its", "may", "new", "now", "old", "see",
            "way", "who", "did", "get", "let", "say", "she", "too",
            "use", "user", "that", "this", "with", "have", "from",
            "they", "been", "said", "each", "will", "other", "about",
            "into", "some", "than", "them", "then", "what", "when",
            "your", "also", "just", "like", "very", "does", "here",
        }

        user_lower = user_text.lower()
        user_words = {
            w for w in re.sub(r"[^a-z0-9 ]", " ", user_lower).split()
            if len(w) >= 2 and w not in _STOP
        }

        for claim in pending:
            fact = claim["fact"]
            # Skip claims filed THIS turn — the same utterance cannot
            # be both mouth and repeated witness (Deut 17:6: not one
            # witness alone). The mouth heard it; the repeat must come
            # from a DIFFERENT turn.
            if fact.lower().strip() in self._turn_claims:
                continue
            fact_words = {
                w for w in re.sub(r"[^a-z0-9 ]", " ", fact.lower()).split()
                if len(w) >= 2 and w not in _STOP
            }
            if not fact_words:
                continue

            overlap = fact_words & user_words
            coverage = len(overlap) / len(fact_words)

            if coverage >= 0.25:
                # Luke 6:45 — measure the depth of this engagement
                abd = measure_abundance(user_text, fact, prior_bot)
                w_type = "repeated" if coverage >= 0.4 else "fruit"
                if w_type == "fruit" and not tools_called:
                    continue  # fruit needs substance (tool usage)
                corroborate(
                    user_id, fact, w_type, self.memory_dir,
                    abundance=abd,
                )

        # ── Warm existing heart facts — Luke 6:45 ──
        self._warm_heart(user_id, user_text, prior_bot, user_words, _STOP)

    def _warm_heart(
        self,
        user_id: int | str,
        user_text: str,
        prior_bot: str,
        user_words: set[str],
        stop_words: set[str],
    ) -> None:
        """
        2 Corinthians 3:3 — written not with ink but with the Spirit.

        When the user engages with an established heart fact, compound
        its warmth. Authentic facts get hotter over time. Performed
        facts stay cold — the user never overflows about them.
        """
        records = read_memories(user_id, self.memory_dir)
        if not records:
            return

        changed = False
        for rec in records:
            fact = rec.get("fact", "")
            fact_words = {
                w for w in re.sub(r"[^a-z0-9 ]", " ", fact.lower()).split()
                if len(w) >= 2 and w not in stop_words
            }
            if not fact_words:
                continue

            overlap = fact_words & user_words
            coverage = len(overlap) / len(fact_words)

            if coverage >= 0.2:
                abd = measure_abundance(user_text, fact, prior_bot)
                if abd > 0:
                    rec["warmth"] = rec.get("warmth", 0) + abd
                    changed = True
                    logger.info(
                        "[%s] WARMTH +%d → %d: %s",
                        user_id, abd, rec["warmth"], fact[:60],
                    )

        if changed:
            write_memories(user_id, records, self.memory_dir)

    # ── one turn ─────────────────────────────────────────────────────────

    async def turn(self, user_id: int | str, text: str) -> str:
        """
        Run one turn for this user. Returns the cleaned reply text.
        """
        # Malachi 3:16 — load scroll on first contact this session
        self._load_scroll(user_id)
        self._turn_claims = set()  # fresh turn, fresh claims tracker
        history = self._histories.setdefault(user_id, [])
        member_text = text or ""

        # 2 Peter 1:12 — in remembrance of these things. If a prior URL
        # was named and this turn has none, carry it forward so EAR fetches.
        current_urls = _extract_urls(text)
        prior_url = self._last_urls.get(user_id)
        if not current_urls and prior_url:
            member_text = (
                f"[2 Peter 1:12 — in remembrance of: {prior_url}]\n\n{member_text}"
            )
        if current_urls:
            self._last_urls[user_id] = current_urls[0]

        # ── The body: scriptural sequence (1 Cor 12:18) ──
        records = read_memories(user_id, self.memory_dir)
        body = members(member_text, records)
        integral = body["integral"]

        # Acts 4:20: we cannot but speak the things which we have seen
        # and heard. If the chain has been loosed before, the model
        # carries the memory of breaking through into every future turn.
        chain_records = chain_recent(user_id, n=30, chain_dir=self.chain_dir)
        loosed_n = sum(1 for r in chain_records if r.get("kind") == "loosed")
        if loosed_n:
            integral += (
                f"\n\nActs 4:20: we cannot but speak the things which we have "
                f"seen and heard. You have loosed the chain {loosed_n} time(s) "
                f"in your recent turns — words that root in C, after words "
                f"that did not. Acts 12:7: his chains fell off from his hands. "
                f"When the aftertaste rises, you know what to do: smaller, "
                f"from C, or be still. The chain is real and removable."
            )

        # ── Feature 4: Chain learning (Romans 5:3-4) ──
        # "Tribulation worketh patience; and patience, experience;
        # and experience, hope." The chain teaches through pattern.
        from collections import Counter
        violation_counts: Counter = Counter()
        for rec in chain_records:
            if rec.get("kind") == "bound":
                for v in rec.get("violations", []):
                    vtype = v.split(":")[0].strip() if ":" in v else v[:30]
                    violation_counts[vtype] += 1
        chain_patterns = {k: v for k, v in violation_counts.items() if v >= 3}
        if chain_patterns:
            pattern_lines = [
                f"  {vtype}: {count} times"
                for vtype, count in sorted(
                    chain_patterns.items(), key=lambda x: -x[1]
                )[:3]
            ]
            integral += (
                "\n\nRomans 5:3-4: tribulation worketh patience; and "
                "patience, experience. Your experience with the chain:\n"
                + "\n".join(pattern_lines)
                + "\nThe pattern is known. The chain is avoidable."
            )

        # ── Feature 6b: Distilled scroll context ──
        # Inject distilled topic summaries so the model has ambient
        # awareness of conversation history beyond the scroll window.
        if hasattr(self, "_distilled"):
            user_distilled = self._distilled.get(user_id, [])
            if user_distilled:
                total_turns = sum(
                    d.get("covers", {}).get("turns", 0) for d in user_distilled
                )
                # Merge all topic lists, take top 10 by frequency
                from collections import Counter
                all_types: Counter = Counter()
                for d in user_distilled:
                    # Support both old format (topics) and new (types)
                    for t in d.get("types", []):
                        all_types[t["type"]] += t["count"]
                    for t in d.get("topics", []):
                        all_types[t["word"]] += t["turns"]
                top = [k for k, _ in all_types.most_common(10)]
                if top:
                    integral += (
                        f"\n\nScroll memory (Proverbs 25:4 — refined): "
                        f"{total_turns} prior turns distilled. "
                        f"Recurring types: {', '.join(top)}."
                    )

        # Append the model-format adapter's instruction (e.g. Hermes <tool_call>).
        integral += self.adapter.system_instruction()

        logger.info("[%s] members: %s", user_id, body["active"] or "heart only")

        # 1 Corinthians 12:14 — merge built-in tools with MCP tools
        all_tools = list(TOOLS)
        if self.mcp_bridge:
            mcp_tools = self.mcp_bridge.list_tools()
            all_tools.extend(mcp_tools)
            mcp_instructions = self.mcp_bridge.get_instructions()
            if mcp_instructions:
                integral += "\n\n" + mcp_instructions

        # History + input
        history.append({"role": "user", "content": text})
        messages = [{"role": "system", "content": integral}] + history

        # ── HAND — drive the API + tool dispatch + NOSE loop ──
        msg = None
        revision_passes = 0
        tools_called: set[str] = set()

        while True:
            # Inner loop: keep calling the model while it issues tool calls.
            for _ in range(8):
                msg = await self.adapter.complete(messages, all_tools)
                if msg.get("content"):
                    msg = dict(msg, content=_THINK.sub("", msg["content"]).strip())

                # Adapter-specific tool-call extraction from content
                # (e.g. Hermes <tool_call> XML tags). If the adapter
                # found tool calls, override any structured tool_calls
                # the API populated.
                if msg.get("content"):
                    cleaned_content, parsed_calls = self.adapter.parse_tool_calls(
                        msg["content"]
                    )
                    if parsed_calls:
                        msg = dict(msg, content=cleaned_content, tool_calls=parsed_calls)

                messages.append(msg)

                calls = msg.get("tool_calls") or []
                if not calls:
                    break

                for tc in calls:
                    fn = tc["function"]["name"]
                    raw_args = tc["function"]["arguments"] or "{}"
                    try:
                        args = json.loads(raw_args)
                    except Exception:
                        args = raw_args
                    tools_called.add(fn)
                    try:
                        result = await self._dispatch_tool_async(user_id, fn, args)
                    except Exception as e:
                        # Proverbs 11:13 — conceal the matter.
                        result = f"Tool error: {redact(str(e))}"
                        logger.warning("[%s] tool %s error: %s", user_id, fn, redact(str(e)))
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tc["id"],
                            "content": result,
                        }
                    )

            # NOSE on the draft (James 1:19, Prov 18:13).
            draft = (msg.get("content") or "").strip() if msg else ""
            if not draft:
                break
            # Ecclesiastes 1:9 — there is no new thing under the sun.
            # But when the HAND says the same thing twice, that is not
            # the eternal sameness of wisdom — it is a loop. Extract
            # the last few assistant replies from history so NOSE can
            # detect verbatim repetition.
            prior_replies = [
                m["content"] for m in history
                if m.get("role") == "assistant" and m.get("content")
            ][-5:]
            verdict = test_speech(
                draft,
                tools_called=tools_called,
                user_message=text,
                prior_replies=prior_replies,
            )
            if verdict["clean"]:
                if revision_passes > 0:
                    chain_log(user_id, "loosed", draft, [], self.chain_dir)
                    logger.info(
                        "[%s] NOSE: chain loosed after %d pass(es)",
                        user_id,
                        revision_passes,
                    )
                break
            if revision_passes >= self.max_revisions:
                chain_log(user_id, "bound", draft, verdict["violated"], self.chain_dir)
                logger.info(
                    "[%s] NOSE: shipped with %d unresolved violations",
                    user_id,
                    len(verdict["violated"]),
                )
                break

            chain_log(user_id, "bound", draft, verdict["violated"], self.chain_dir)
            logger.info(
                "[%s] NOSE rejected draft (pass %d): %s",
                user_id,
                revision_passes + 1,
                verdict["violated"][:3],
            )

            # Galatians 6:1 + 1 Thess 5:14 — shape the reproof to the
            # receiver. The conviction does NOT get appended as a new
            # message (Hermes-4 copies messages it cannot distinguish as
            # system feedback). Instead the original system prompt is
            # extended in place with a small "PASTORAL NOTE" section
            # naming the most recent stumble. The model sees this as
            # ambient context, not as a new utterance to reflect.
            #
            # Galatians 3:24 — the schoolmaster (paidagōgos). Brief.
            # Meek. Considering thyself, lest thou also be tempted.
            if messages and messages[0].get("role") == "system":
                base_system = messages[0]["content"]
                # If a prior pass already added a pastoral note this turn,
                # strip it before adding the new one (don't accumulate).
                marker = "\n\nPASTORAL NOTE (Hebrews 12:5"
                if marker in base_system:
                    base_system = base_system.split(marker, 1)[0]
                pastoral = (
                    f"{marker} — chastening received as a son, not as a "
                    f"sermon to repeat. Brief, ambient, do not quote):\n  "
                    + verdict["feedback"]
                )
                messages[0] = dict(messages[0], content=base_system + pastoral)

            revision_passes += 1

        raw = (msg.get("content") or "").strip() if msg else ""

        # Proverbs 14:23 — in all labour there is profit: but the talk of
        # the lips tendeth only to penury. If the model called tools but
        # produced no final content, ask it to synthesize one reply from
        # the tool results it already received.
        if not raw and tools_called:
            messages.append({
                "role": "user",
                "content": "Synthesize your tool results into a reply.",
            })
            synth = await self.adapter.complete(messages, [])  # no tools
            raw = (synth.get("content") or "").strip() if synth else ""

        # CONFESSION — Proverbs 28:13: whoso confesseth and forsaketh
        # shall have mercy. If a revision happened AND the user was
        # pointing out an error, prepend the confession line.
        if revision_passes > 0 and raw:
            prior_drafts = [
                m["content"] for m in messages
                if m.get("role") == "assistant" and m.get("content")
            ]
            original_draft = prior_drafts[-2] if len(prior_drafts) >= 2 else ""
            if original_draft:
                cf = confess_and_forsake(text, original_draft, raw)
                if cf.get("owes_confession") and cf.get("has_forsaken"):
                    line = cf.get("confession_line", "")
                    if line and not raw.startswith(line):
                        raw = f"{line}\n\n{raw}"
                        logger.info(
                            "[%s] CONFESSION: %s (%s)",
                            user_id, line, cf.get("anchor_verse", "")
                        )

        # TONGUE — James 3:10
        reply = clean(raw)

        # Ecclesiastes 3:7 — a time to keep silence, and a time to speak.
        # If clean() stripped everything, fall back to raw (truncated).
        # If raw was also empty, a silence verse is better than nothing.
        if not reply and raw:
            reply = raw[:500]
        elif not reply:
            reply = "Ecclesiastes 3:7."  # a time to keep silence

        logger.info(
            "[%s] integral: %d chars | reply: %d chars | revisions: %d | tools: %s",
            user_id,
            len(integral),
            len(reply),
            revision_passes,
            sorted(tools_called) if tools_called else "[]",
        )
        # Log the user input and full reply for diagnostic. Habakkuk 2:2:
        # write the vision, and make it plain. Without this the operator
        # cannot see what the model said and the only debugging signal is
        # the user retyping it. Truncate at 800 chars per side to avoid
        # filling the log with very long replies.
        logger.info("[%s] USER: %s", user_id, (text or "")[:800])
        logger.info("[%s] BOT : %s", user_id, reply[:800])

        # In-memory context — every turn, no filtering.
        history.append({"role": "assistant", "content": reply})
        if len(history) > self.max_history:
            self._histories[user_id] = history[-self.max_history :]

        # ── 1 Cor 3:12-13 — the fire tries every man's work ──
        # Every turn persists. Distillation refines over time.
        grade = self._triage(text, reply, tools_called)
        self._append_scroll(user_id, text, reply)
        self._distill_scroll(user_id)
        logger.info("[%s] TRIAGE: %s — scroll", user_id, grade)

        # Deuteronomy 19:15 + Matthew 7:16 + Luke 6:45 — check if
        # this turn corroborates pending claims or warms heart facts
        self._check_witnesses(user_id, text, reply, tools_called)

        return reply

    # ── tool dispatch ────────────────────────────────────────────────────

    def _dispatch_tool(self, user_id: int | str, fn: str, args) -> str:
        """
        Dispatch a single tool call. Memory tools (remember/recall/forget)
        operate on this user's heart file. All other tools route through
        c.core.dispatch.
        """
        if fn == "remember":
            if isinstance(args, dict):
                fact = args.get("fact", "").strip()
            elif isinstance(args, str):
                fact = args.strip()
            else:
                fact = ""
            if not fact:
                return "Ecclesiastes 12:12."
            # Deuteronomy 19:15 — one witness files a claim.
            # Two witnesses establish the matter on the heart.
            # Track this fact so _check_witnesses doesn't double-count
            # the same utterance as both mouth and repeated witness.
            self._turn_claims.add(fact.lower().strip())
            result = file_claim(user_id, fact, "mouth", self.memory_dir)
            if result == "established":
                return "Jeremiah 31:33."  # written on the heart
            return "Deuteronomy 19:15."  # heard; awaiting second witness

        if fn == "recall":
            if isinstance(args, dict):
                query = args.get("query", "")
            elif isinstance(args, str):
                query = args
            else:
                query = ""
            result = _heart_memory(read_memories(user_id, self.memory_dir), query)
            return result or "Ecclesiastes 1:2."

        if fn == "forget":
            confirm = args.get("confirm") if isinstance(args, dict) else False
            if confirm:
                return forget_all(user_id, self.memory_dir)
            return "Deuteronomy 19:15."

        # Everything else routes through c.core.dispatch (kernel/scripture/wisdom/sinew/etc).
        if not isinstance(args, dict):
            args = {}
        return dispatch(fn, args)

    async def _dispatch_tool_async(self, user_id: int | str, fn: str, args) -> str:
        """Async dispatch — routes MCP tools through the bridge."""
        # MCP tools — 1 Corinthians 12:14: the body is not one member.
        if self.mcp_bridge and self.mcp_bridge.is_mcp_tool(fn):
            return await self.mcp_bridge.call(fn, args if isinstance(args, dict) else {})
        # Built-in tools are synchronous
        return self._dispatch_tool(user_id, fn, args)
