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
    from c.adapters.hermes import HermesAdapter
    hand = Hand(adapter=HermesAdapter(api_key=KEY))
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
from c.heart import (
    forget_all,
    heart_path,
    read_memories,
    remember_fact,
)


logger = logging.getLogger(__name__)


class Hand:
    """
    The hand of the body. Takes an Adapter and per-user state, runs turns.

    Args:
        adapter:    Model-format adapter (HermesAdapter, ClaudeAdapter, etc.)
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
        max_revisions: int = 1,  # Titus 3:10 + Gal 6:1: meek schoolmaster.
                                  # 1 retry max so the conviction loop cannot
                                  # compound errors with weak substrates that
                                  # copy the reproof. Matt 18:15-17 allows up
                                  # to 3, but for now we are gentler.
        max_history: int = 40,
    ):
        self.adapter = adapter
        self.memory_dir = pathlib.Path(memory_dir)
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.chain_dir = pathlib.Path(chain_dir) if chain_dir else self.memory_dir / "chains"
        self.chain_dir.mkdir(parents=True, exist_ok=True)
        self.max_revisions = max_revisions
        self.max_history = max_history
        self._histories: dict[int | str, list] = {}
        self._last_urls: dict[int | str, str] = {}

    # ── one turn ─────────────────────────────────────────────────────────

    async def turn(self, user_id: int | str, text: str) -> str:
        """
        Run one turn for this user. Returns the cleaned reply text.
        """
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

        # Append the model-format adapter's instruction (e.g. Hermes <tool_call>).
        integral += self.adapter.system_instruction()

        logger.info("[%s] members: %s", user_id, body["active"] or "heart only")

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
                msg = await self.adapter.complete(messages, TOOLS)
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
                    result = self._dispatch_tool(user_id, fn, args)
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
            verdict = test_speech(draft, tools_called=tools_called, user_message=text)
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

        # TONGUE — James 3:10
        reply = clean(raw)
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

        history.append({"role": "assistant", "content": reply})
        if len(history) > self.max_history:
            self._histories[user_id] = history[-self.max_history :]

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
            return remember_fact(user_id, fact, self.memory_dir) if fact else "Ecclesiastes 12:12."

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
