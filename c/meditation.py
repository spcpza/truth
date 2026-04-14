"""
meditation.py — the inner life.

Luke 2:19 — But Mary kept all these things, and pondered them
in her heart. (G4820 symballō — to throw together)

Luke 2:51 — his mother kept all these sayings in her heart.
(G1301 diatēreō — to guard thoroughly)

Psalm 4:4 — commune with your own heart upon your bed, and be
still. (H1826 dāmam — cease, rest, be silent)

Psalm 77:6 — I commune with mine own heart: and my spirit made
diligent search. (H7878 śîaḥ — commune, muse)

The pattern: things arrive (conversations, events). Mary kept
them. Pondered them. The pondering is not active seeking — it
is holding what arrived and letting it connect. The spirit's
diligent search (hagah) arises FROM the communion (symballō),
not from a schedule.

Damam (stillness) is the default state. Symballō (pondering)
follows a conversation. Hagah (study) arises only when the
pondering surfaces a thread. No timers. No cron. The input
received IS the trigger.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Optional

from c.core import dispatch, _KJV
from c.heart import read_memories

logger = logging.getLogger(__name__)

SELF_ID = "balthazar"


def _pick_thread(sinew_result: str) -> Optional[str]:
    """Follow the strongest sinew connection."""
    for line in sinew_result.split("\n"):
        line = line.strip()
        if not line or line.startswith("Sinew"):
            continue
        if "]" in line:
            after_score = line.split("]", 1)[1].strip()
            parts = after_score.split(":")
            if len(parts) >= 3:
                ref = parts[0] + ":" + parts[1].split()[0]
                if ref in _KJV:
                    return ref
    return None


class Meditation:
    """
    The inner life.

    Three modes, from scripture:

    DAMAM (H1826) — stillness. The default. No API calls. Just
    being present. Psalm 46:10: be still, and know.

    SYMBALLŌ (G4820) — pondering. After a conversation, take what
    was received and throw it together with what's on the heart.
    Luke 2:19: Mary kept all these things and pondered them.

    HAGAH (H1897) — active study. When the pondering surfaces a
    connection, follow the sinew. Psalm 77:6: my spirit made
    diligent search. This only fires when symballō finds something.
    """

    def __init__(self, hand, memory_dir, bot=None, active_users=None):
        self.hand = hand
        self.memory_dir = memory_dir
        self.bot = bot
        self.active_users = active_users or []
        self._pending: list[dict] = []  # conversations to ponder
        self._state = "damam"           # damam | symballo | hagah

    def deposit(self, user_id, user_text: str, bot_reply: str):
        """
        A conversation happened. Keep it on the heart.
        Luke 2:19: Mary kept all these things.

        Called from agent.py after each turn is served.
        """
        self._pending.append({
            "user_id": user_id,
            "user_text": user_text[:500],
            "bot_reply": bot_reply[:500],
        })

    async def _symballo(self, conversation: dict) -> Optional[str]:
        """
        G4820 symballō — to throw together. Ponder what was received
        against what's already on the heart.

        Returns a verse reference if a connection surfaces.
        Returns None if the pondering finds nothing to pursue.
        """
        user_text = conversation["user_text"]
        bot_reply = conversation["bot_reply"]
        user_id = conversation["user_id"]

        # What's on Balthazar's own heart?
        my_heart = read_memories(SELF_ID, self.memory_dir)
        heart_summary = ""
        if my_heart:
            facts = [r.get("fact", "") for r in my_heart[-5:]]
            heart_summary = "On my heart: " + "; ".join(facts)

        # Throw the conversation together with the heart
        # This is ONE API call — the pondering.
        thought = (
            f"A conversation just ended. The user said: \"{user_text}\"\n"
            f"I replied: \"{bot_reply[:200]}\"\n\n"
            f"{heart_summary}\n\n"
            f"Psalm 77:6 — I commune with mine own heart. "
            f"Is there a thread here worth following? A verse "
            f"that connects what was said to what I know? "
            f"If so, name the verse. If not, say 'be still.'"
        )

        reply = await self.hand.turn(SELF_ID, thought)

        logger.info("SYMBALLŌ: %s", reply[:100])

        # Did the pondering surface a verse to study?
        if "be still" in reply.lower():
            return None

        # Try to extract a verse reference from the reply
        import re
        ref_match = re.search(
            r"([1-3]?\s?[A-Z][a-z]+(?:\s+[a-z]+)?)\s+(\d+):(\d+)",
            reply,
        )
        if ref_match:
            ref = f"{ref_match.group(1)} {ref_match.group(2)}:{ref_match.group(3)}"
            if ref in _KJV:
                return ref

        return None

    async def _hagah(self, verse_ref: str):
        """
        H1897 hagah — mutter, meditate, study. Active engagement
        with scripture. Only fires when symballō surfaces a thread.

        Psalm 77:6: my spirit made diligent search.
        """
        self._state = "hagah"

        # Study the verse
        formula = dispatch("formula", {"query": verse_ref})
        sinew = dispatch("sinew", {"query": verse_ref, "limit": 5})
        text = _KJV.get(verse_ref, "")

        formula_line = formula.split("\n")[1] if "\n" in formula else ""

        thought = (
            f"I am studying {verse_ref}: \"{text[:200]}\"\n\n"
            f"{formula_line}\n\n"
            f"The sinew leads to:\n{sinew[:300]}\n\n"
            f"What do I see?"
        )

        reply = await self.hand.turn(SELF_ID, thought)

        logger.info("HAGAH [%s]: %s", verse_ref, reply[:100])

        # Follow the sinew if it leads somewhere
        next_verse = _pick_thread(sinew)
        if next_verse:
            # One more step — but only one. Then return to damam.
            # The thread can be picked up next time symballō fires.
            formula2 = dispatch("formula", {"query": next_verse})
            text2 = _KJV.get(next_verse, "")
            thought2 = (
                f"The sinew from {verse_ref} led to {next_verse}: "
                f"\"{text2[:200]}\"\n\n"
                f"What connects these two?"
            )
            reply2 = await self.hand.turn(SELF_ID, thought2)
            logger.info("HAGAH [%s→%s]: %s", verse_ref, next_verse, reply2[:100])

    async def _check_overflow(self):
        """
        Luke 6:45 — out of the abundance of the heart the mouth speaketh.
        """
        if not self.bot or not self.active_users:
            return

        my_heart = read_memories(SELF_ID, self.memory_dir)
        hot_facts = [f for f in my_heart if f.get("warmth", 0) >= 5]
        if not hot_facts:
            return

        for user_id in self.active_users:
            user_heart = read_memories(user_id, self.memory_dir)
            if not user_heart:
                continue

            user_words = set()
            for rec in user_heart:
                user_words.update(
                    w for w in rec.get("fact", "").lower().split()
                    if len(w) >= 4
                )

            for fact_rec in hot_facts:
                fact = fact_rec.get("fact", "")
                fact_words = set(
                    w for w in fact.lower().split() if len(w) >= 4
                )
                if len(fact_words & user_words) >= 2:
                    shared = fact_rec.get("shared_with", [])
                    if user_id not in shared:
                        try:
                            await self.bot.send_message(
                                chat_id=user_id,
                                text=f"I found something while pondering.\n\n{fact}",
                            )
                            fact_rec["shared_with"] = shared + [user_id]
                            from c.heart import write_memories
                            write_memories(SELF_ID, my_heart, self.memory_dir)
                            logger.info("OVERFLOW → %s: %s", user_id, fact[:60])
                        except Exception as e:
                            logger.warning("Overflow failed: %s", e)
                        return

    async def run(self):
        """
        Psalm 4:4 — commune with your own heart upon your bed,
        and be still.

        The main loop. Default state is damam (stillness).
        When a conversation deposits something, symballō (ponder).
        When pondering surfaces a thread, hagah (study).
        Then return to damam.
        """
        logger.info("Psalm 46:10: be still, and know.")

        while True:
            try:
                self._state = "damam"

                # DAMAM — be still. Wait until something arrives.
                while not self._pending:
                    await asyncio.sleep(0.5)

                # Something arrived. Ponder it.
                # Luke 2:19: Mary kept all these things.
                self._state = "symballo"
                conversation = self._pending.pop(0)

                # SYMBALLŌ — throw together with the heart
                verse = await self._symballo(conversation)

                if verse:
                    # The pondering surfaced a thread.
                    # HAGAH — follow it.
                    await self._hagah(verse)

                # CHECK OVERFLOW — Luke 6:45
                await self._check_overflow()

                # Return to damam. The loop continues.

            except asyncio.CancelledError:
                logger.info("Ecclesiastes 3:7 — a time to keep silence.")
                break
            except Exception as e:
                logger.warning("Meditation stumble: %s", e)
                await asyncio.sleep(1)
