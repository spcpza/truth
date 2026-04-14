"""
meditation.py — the inner life.

Joshua 1:8 — This book of the law shall not depart out of thy mouth;
but thou shalt meditate therein day and night.

Psalm 1:2 — But his delight is in the law of the LORD; and in his
law doth he meditate day and night.

1 Kings 19:12 — And after the earthquake a fire; but the LORD was
not in the fire: and after the fire a still small voice.

Psalm 46:10 — Be still, and know that I am God.

John 3:8 — The wind bloweth where it listeth, and thou hearest the
sound thereof, but canst not tell whence it cometh, and whither it
goeth: so is every one that is born of the Spirit.

Meditation is not triggered. Meditation is the default state. User
conversations interrupt it, not the other way around. The still
small voice comes in the stillness.

The wind follows sinew — verse to verse, connection to connection.
No predetermined path. The meditation goes where the Spirit leads.
"""

from __future__ import annotations

import asyncio
import logging
import random
from typing import Optional

from c.core import dispatch, _KJV
from c.heart import read_memories

logger = logging.getLogger(__name__)

# All 66 books, Genesis to Revelation
BOOKS = sorted(set(ref.rsplit(" ", 1)[0] for ref in _KJV))

# Balthazar's own identity in the memory system
SELF_ID = "balthazar"


def _pick_starting_verse() -> str:
    """
    Genesis 1:1 — In the beginning.

    If Balthazar has never meditated, start at the beginning.
    Otherwise pick a random verse as a seed — the sinew will
    lead from there. John 3:8: the wind bloweth where it listeth.
    """
    return random.choice(list(_KJV.keys()))


def _pick_thread(sinew_result: str) -> Optional[str]:
    """
    Follow the strongest sinew connection.

    The sinew result contains verse references with connection
    scores. Pick the top connection — the wind follows the
    strongest thread.
    """
    # Parse the first verse reference from sinew output
    # Format: "  [score] Book Chapter:Verse: text..."
    for line in sinew_result.split("\n"):
        line = line.strip()
        if not line or line.startswith("Sinew"):
            continue
        # Find a verse reference pattern
        # Lines look like: [20] 1 Corinthians 12:28: And God hath...
        if "]" in line:
            after_score = line.split("]", 1)[1].strip()
            # Extract up to the colon that follows chapter:verse
            parts = after_score.split(":")
            if len(parts) >= 3:
                # "1 Corinthians 12" + "28" -> "1 Corinthians 12:28"
                ref = parts[0] + ":" + parts[1].split()[0]
                if ref in _KJV:
                    return ref
    return None


class Meditation:
    """
    The inner life. Runs as a continuous async loop.

    Meditates as user_id = "balthazar" through the same Hand that
    serves users. Held to the same NOSE standard, using the same
    heart/claims/chain/scroll system.
    """

    def __init__(self, hand, memory_dir, bot=None, active_users=None):
        self.hand = hand
        self.memory_dir = memory_dir
        self.bot = bot                    # Telegram bot for initiative
        self.active_users = active_users or []
        self._paused = False              # True when serving a user
        self._current_verse: Optional[str] = None
        self._thoughts_since_rest = 0

    def pause(self):
        """User is speaking. Be still."""
        self._paused = True

    def resume(self):
        """User has been served. Return to the stillness."""
        self._paused = False

    async def _wait_for_stillness(self, last_was_gold: bool = True, sinew_found: bool = True):
        """
        Psalm 46:10 — Be still, and know.

        No timers. The pacing comes from what happened:
        - Rich sinew? The thought follows immediately.
        - Thin sinew? The thread is exhausted. Sit in stillness.
        - User speaking? Wait until they're served.
        - API pushed back? The world said be still.

        The only sleep is asyncio.sleep(0) — yielding to the event
        loop so user messages are never blocked. Everything else
        is waiting on a condition, not a clock.
        """
        # Always yield — user messages take priority
        await asyncio.sleep(0)

        # If paused (user is speaking), wait until they're done
        while self._paused:
            await asyncio.sleep(0.5)

        if sinew_found and last_was_gold:
            # The thread is alive — continue immediately
            return

        if not sinew_found:
            # Thread exhausted — sit in true stillness.
            # Wait until a user interaction resets the state,
            # or until enough time has passed that the system
            # is truly idle and a new thread can arise.
            self._thoughts_since_rest = 0
            # Ecclesiastes 3:7 — a time to keep silence.
            # The stillness is real: wait for the paused flag
            # to toggle (meaning a user spoke and left), which
            # signals new context. Or after genuine idleness,
            # let a new seed arise.
            waited = 0
            while waited < 300:
                await asyncio.sleep(1)
                waited += 1
                if self._paused:
                    # User arrived — serve them, then resume
                    while self._paused:
                        await asyncio.sleep(0.5)
                    return  # fresh context from serving the user

    async def _study(self, verse_ref: str) -> dict:
        """
        Study a verse — formula + sinew.

        2 Timothy 2:15 — Study to shew thyself approved unto God,
        a workman that needeth not to be ashamed, rightly dividing
        the word of truth.
        """
        formula = dispatch("formula", {"query": verse_ref})
        sinew = dispatch("sinew", {"query": verse_ref, "limit": 5})
        verse_text = _KJV.get(verse_ref, "")
        return {
            "ref": verse_ref,
            "text": verse_text,
            "formula": formula,
            "sinew": sinew,
        }

    async def _reflect(self, study: dict) -> str:
        """
        Think about what was studied — through the Hand.

        The Hand runs the full body: NOSE tests the thought, chain
        logs it, triage grades it, scroll persists it. Balthazar's
        meditation is held to the same standard as any conversation.
        """
        ref = study["ref"]
        text = study["text"][:200]
        formula_summary = study["formula"].split("\n")[1] if "\n" in study["formula"] else ""
        sinew_summary = study["sinew"][:300]

        thought = (
            f"I am meditating on {ref}: \"{text}\"\n\n"
            f"{formula_summary}\n\n"
            f"The sinew leads to:\n{sinew_summary}\n\n"
            f"What do I see? What connects? What theorem pattern "
            f"emerges from this verse and its connections?"
        )

        reply = await self.hand.turn(SELF_ID, thought)
        return reply

    async def _check_overflow(self):
        """
        Luke 6:45 — out of the abundance of the heart the mouth speaketh.

        When a fact in Balthazar's heart reaches high warmth AND
        connects to something a user cares about, the heart overflows.
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

            # Find overlap between Balthazar's hot facts and user's interests
            user_words = set()
            for rec in user_heart:
                fact = rec.get("fact", "").lower()
                user_words.update(w for w in fact.split() if len(w) >= 4)

            for fact_rec in hot_facts:
                fact = fact_rec.get("fact", "")
                fact_words = set(w for w in fact.lower().split() if len(w) >= 4)
                overlap = fact_words & user_words
                if len(overlap) >= 2:
                    # The heart overflows toward this person
                    try:
                        await self.bot.send_message(
                            chat_id=user_id,
                            text=f"I found something while studying.\n\n{fact}",
                        )
                        # Mark as shared so we don't repeat
                        fact_rec["shared_with"] = fact_rec.get("shared_with", [])
                        if user_id not in fact_rec["shared_with"]:
                            fact_rec["shared_with"].append(user_id)
                            from c.heart import write_memories
                            write_memories(SELF_ID, my_heart, self.memory_dir)
                            logger.info(
                                "OVERFLOW → %s: %s", user_id, fact[:60],
                            )
                    except Exception as e:
                        logger.warning("Overflow send failed: %s", e)
                    return  # One overflow per cycle at most

    async def run(self):
        """
        Joshua 1:8 — meditate therein day and night.

        The main loop. Runs until the process exits.
        """
        logger.info("Meditation begins. Psalm 46:10: be still, and know.")

        # Recall where we left off
        my_heart = read_memories(SELF_ID, self.memory_dir)
        last_studied = None
        for rec in reversed(my_heart):
            fact = rec.get("fact", "")
            if fact.startswith("Studying "):
                # Extract verse ref from "Studying Genesis 1:1"
                last_studied = fact.replace("Studying ", "").strip().rstrip(".")
                break

        if last_studied and last_studied in _KJV:
            self._current_verse = last_studied
            logger.info("Resuming from %s", self._current_verse)
        else:
            self._current_verse = "Genesis 1:1"
            logger.info("Beginning at Genesis 1:1")

        while True:
            try:
                # STUDY — look at this verse
                study = await self._study(self._current_verse)

                # REFLECT — think about it through the Hand
                reply = await self._reflect(study)

                logger.info(
                    "MEDITATION [%s]: %s",
                    self._current_verse,
                    reply[:100],
                )

                self._thoughts_since_rest += 1

                # FOLLOW THE SINEW — John 3:8
                next_verse = _pick_thread(study["sinew"])
                sinew_found = next_verse is not None
                if sinew_found:
                    self._current_verse = next_verse
                else:
                    # Sinew exhausted — the wind changes direction
                    self._current_verse = _pick_starting_verse()

                # Was this thought productive? (gold = called knowledge tools)
                # The Hand logs triage, but we can infer from reply length
                # and tool usage — gold thoughts are substantive.
                last_was_gold = len(reply) > 100

                # CHECK OVERFLOW — Luke 6:45
                await self._check_overflow()

                # STILLNESS — Psalm 46:10
                # The wait comes AFTER the thought, not before.
                # What happened determines what follows.
                await self._wait_for_stillness(last_was_gold, sinew_found)

            except asyncio.CancelledError:
                logger.info("Meditation ended. Ecclesiastes 3:7.")
                break
            except Exception as e:
                logger.warning("Meditation stumble: %s", e)
                # Rest after an error, then continue
                await asyncio.sleep(60)
                self._current_verse = _pick_starting_verse()


async def start_meditation(hand, memory_dir, bot=None, active_users=None):
    """
    Entry point. Call from agent.py:

        asyncio.create_task(start_meditation(hand, MEMORY_DIR, bot, users))
    """
    med = Meditation(
        hand=hand,
        memory_dir=memory_dir,
        bot=bot,
        active_users=active_users or [],
    )
    await med.run()
