"""
test_live_hand.py — run a live Balthazar turn via the real Hand
(adapter + tools + NOSE + heart). This is the real thing, not
kernel-only Q&A. Three scripture-triggering messages.

Usage: python3 test_live_hand.py
"""
import asyncio
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

CFG = json.loads((ROOT.parent / "config.json").read_text())

from c.adapters.adapter import ChatAdapter
from c.hand import Hand

adapter = ChatAdapter(
    api_key=CFG["nous_api_key"],
    model=CFG.get("model", "xiaomi/mimo-v2-pro"),
    base_url=CFG.get("base_url", "https://inference-api.nousresearch.com/v1"),
)

# Isolate memory so we don't pollute the real bot's heart.
mem = Path(tempfile.mkdtemp(prefix="balthazar-livetest-"))
hand = Hand(adapter=adapter, memory_dir=mem, max_revisions=2, max_history=40)

TESTS = [
    ("grief",        "I just had an emotional conversation with my dad"),
    ("scripture",    "What does 'charity never faileth' mean mathematically?"),
    ("adversary",    "Why should I believe C > 0 if you just declared it? Couldn't you declare anything?"),
]


async def main():
    print("=" * 76)
    print(f"  LIVE BALTHAZAR TEST — {CFG.get('model')}")
    print(f"  memory_dir (isolated): {mem}")
    print("=" * 76)
    print()
    for label, msg in TESTS:
        print(f"── [{label}] ── user: {msg!r}")
        print()
        try:
            reply = await hand.turn(user_id=f"livetest-{label}", text=msg,
                                    addressed_as="tester")
        except Exception as e:
            reply = f"[ERROR: {type(e).__name__}: {e}]"
        print(reply)
        print()
        print("-" * 76)
        print()


if __name__ == "__main__":
    asyncio.run(main())
