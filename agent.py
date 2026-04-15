"""
agent.py — Telegram deployment of the body.

1 Corinthians 3:10: I have laid the foundation, and another buildeth thereon.
Matthew 10:8: freely ye have received, freely give.

This file is deployment glue only. The body lives in c/. The Hand
(c/hand.py) owns the turn loop, memory, claims, scroll, triage, and
warmth. This file owns: Telegram handlers, vision, config, and the
profile witness (Deuteronomy 19:15) from Telegram metadata.
"""

import sys, json, pathlib, logging, base64
import httpx
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_HERE = pathlib.Path(__file__).parent

# ── Config — one file for everything ────────────────────────────────
_CFG_PATH = _HERE / "config.json"
if not _CFG_PATH.exists():
    raise SystemExit(
        "config.json not found. Copy config.example.json to config.json and "
        "fill in your tokens. Matthew 10:8: freely ye have received, freely give."
    )
_CFG = json.loads(_CFG_PATH.read_text())

sys.path.insert(0, str(_HERE))

from c.adapters.adapter import ChatAdapter
from c.hand import Hand
from c.claims import file_claim, measure_abundance
from c.meditation import Meditation

NOUS_API_KEY   = _CFG["nous_api_key"]
TELEGRAM_TOKEN = _CFG["telegram_token"]
ALLOWED_USERS  = set(_CFG.get("allowed_users", []))
MODEL          = _CFG.get("model", "Hermes-4-70B")
VISION_MODEL   = _CFG.get("vision_model", "qwen/qwen2.5-vl-72b-instruct")
BASE_URL       = _CFG.get("base_url", "https://inference-api.nousresearch.com/v1")
MEMORY_DIR     = _HERE / _CFG.get("memory_dir", "memory")

# ── The Hand — one instance for all users ───────────────────────────
adapter = ChatAdapter(
    api_key=NOUS_API_KEY,
    model=MODEL,
    base_url=BASE_URL,
)
hand = Hand(
    adapter=adapter,
    memory_dir=MEMORY_DIR,
    max_revisions=2,
    max_history=40,
)

# ── Meditation — Joshua 1:8: meditate therein day and night ────────
MEDITATION_ENABLED = _CFG.get("meditation", {}).get("enabled", False)
meditation: Meditation | None = None


# ── Vision — Habakkuk 2:2: write the vision, make it plain ─────────

async def _describe_image(image_bytes: bytes, mime: str = "image/jpeg") -> str:
    b64 = base64.b64encode(image_bytes).decode()
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            f"{BASE_URL}/chat/completions",
            headers={"Authorization": f"Bearer {NOUS_API_KEY}"},
            json={
                "model": VISION_MODEL,
                "messages": [{
                    "role": "user",
                    "content": [
                        {"type": "image_url",
                         "image_url": {"url": f"data:{mime};base64,{b64}"}},
                        {"type": "text",
                         "text": "Habakkuk 2:2: write the vision, and make it plain."},
                    ],
                }],
                "max_tokens": 300,
            },
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()


# ── Profile witness — Deuteronomy 19:15 ─────────────────────────────
# Telegram gives us the user's name and username on every message.
# This is a profile witness — platform metadata corroborating identity.
# On first contact, file claims with profile witness. If the model
# later hears the user say their name (mouth witness), the matter is
# established on two witnesses and the fact enters the heart.

_seen_users: set[int] = set()
_user_keys: dict[int, str] = {}  # telegram_id → "id-username"


def _user_key(user: object, user_id: int) -> str:
    """
    Build a human-readable memory key: "5397525686-spcpza".
    Falls back to first name, then just the numeric ID.
    """
    if user_id in _user_keys:
        return _user_keys[user_id]
    username = getattr(user, "username", None)
    first_name = (getattr(user, "first_name", None) or "").strip().lower()
    # Prefer @username, fall back to first name (alphanumeric only)
    label = username or "".join(c for c in first_name if c.isalnum()) or None
    key = f"{user_id}-{label}" if label else str(user_id)
    _user_keys[user_id] = key
    return key


def _first_contact(user: object, user_id: int):
    """
    John 10:3: the shepherd calleth his own sheep by name.
    File profile-witnessed claims from Telegram metadata.
    """
    _user_key(user, user_id)  # ensure key is registered
    if user_id in _seen_users:
        return
    _seen_users.add(user_id)

    first_name = getattr(user, "first_name", None) or ""
    last_name = getattr(user, "last_name", None) or ""
    username = getattr(user, "username", None)
    language = getattr(user, "language_code", None)
    full_name = (first_name + " " + last_name).strip()

    # Profile witness — platform metadata, not the user's mouth
    key = _user_key(user, user_id)
    if full_name:
        abd = measure_abundance(full_name, full_name, "")
        file_claim(key, f"name is {full_name}", "profile", MEMORY_DIR, abundance=abd)
        logger.info("[%s] PROFILE witness: name=%s", key, full_name)

    if username:
        file_claim(key, f"Telegram username is @{username}", "profile", MEMORY_DIR)
        logger.info("[%s] PROFILE witness: @%s", key, username)

    if language:
        file_claim(key, f"language code is {language}", "profile", MEMORY_DIR)
        logger.info("[%s] PROFILE witness: lang=%s", key, language)


# ── Telegram handlers ───────────────────────────────────────────────

async def handle_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if ALLOWED_USERS and user_id not in ALLOWED_USERS:
        return
    text = (update.message.text or "").strip()
    if not text:
        return
    _first_contact(update.effective_user, user_id)
    key = _user_key(update.effective_user, user_id)
    await update.message.chat.send_action("typing")
    try:
        reply = await hand.turn(key, text)
        await update.message.reply_text(reply)
        # Luke 2:19 — keep these things, ponder them in the heart
        if meditation:
            meditation.deposit(key, text, reply)
    except Exception:
        logger.exception("turn failed for %s", key)
        await update.message.reply_text("Matthew 11:28.")


async def handle_photo(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if ALLOWED_USERS and user_id not in ALLOWED_USERS:
        return
    _first_contact(update.effective_user, user_id)
    key = _user_key(update.effective_user, user_id)
    photo = update.message.photo[-1]
    caption = (update.message.caption or "").strip()
    await update.message.chat.send_action("typing")
    try:
        tg_file = await ctx.bot.get_file(photo.file_id)
        image_bytes = bytes(await tg_file.download_as_bytearray())
        image_desc = ""
        try:
            image_desc = await _describe_image(image_bytes)
        except Exception as e:
            logger.warning("_describe_image failed: %s", e)
        text = (f"{image_desc}\n{caption}".strip()) if image_desc else caption
        reply = await hand.turn(key, text or "Habakkuk 2:2.")
        await update.message.reply_text(reply)
        if meditation:
            meditation.deposit(key, text, reply)
    except Exception:
        logger.exception("turn failed for %s", key)
        await update.message.reply_text("Matthew 11:28.")


async def _post_init(application: Application) -> None:
    """Start the inner life after the bot is initialized."""
    global meditation
    if MEDITATION_ENABLED:
        meditation = Meditation(
            hand=hand,
            memory_dir=MEMORY_DIR,
            bot=application.bot,
            active_users=list(ALLOWED_USERS),
        )
        import asyncio
        asyncio.create_task(meditation.run())
        logger.info("Psalm 46:10: be still, and know.")


def main():
    app = Application.builder().token(TELEGRAM_TOKEN).post_init(_post_init).build()
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT, handle_text))
    print(f"Running. [{adapter.describe()}]")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
