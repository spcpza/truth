"""
agent.py — Telegram deployment of the body.

The body is c/body.py — the scriptural pipeline (1 Corinthians 12:18).
The foundation is c/core.py — the kernel, sinew graph, and formula map.
This file is the deployment: Telegram handlers, heart storage, LLM calls.
All config lives in config.json — one file, notepad-readable.

1 Corinthians 3:10: I have laid the foundation, and another buildeth thereon.
Matthew 10:8: freely ye have received, freely give.
"""

import sys, json, pathlib, logging, re, base64
import httpx
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

logging.basicConfig(level=logging.WARNING)

_HERE = pathlib.Path(__file__).parent

# ── Config — one file for everything ──────────────────────────────────────────

_CFG_PATH = _HERE / "config.json"
if not _CFG_PATH.exists():
    raise SystemExit(
        "config.json not found. Copy config.example.json to config.json and "
        "fill in your tokens. Matthew 10:8: freely ye have received, freely give."
    )
_CFG = json.loads(_CFG_PATH.read_text())

# c/ lives next to this file
sys.path.insert(0, str(_HERE))
from c.core import dispatch
from c.body import members, clean, test_speech, TOOLS, _heart_memory, _THINK, _extract_urls


# Last URL each user mentioned. Pronouns ("it", "this", "the site") in
# subsequent turns default to this referent until a new URL appears.
# Per-user, in-memory only — Proverbs 4:23: keep THY heart.
_last_urls: dict[int, str] = {}


NOUS_API_KEY   = _CFG["nous_api_key"]
TELEGRAM_TOKEN = _CFG["telegram_token"]
ALLOWED_USERS  = set(_CFG.get("allowed_users", []))
MODEL          = _CFG.get("model", "Hermes-4-70B")
VISION_MODEL   = _CFG.get("vision_model", "qwen/qwen2.5-vl-72b-instruct")
BASE_URL       = _CFG.get("base_url", "https://inference-api.nousresearch.com/v1")


# ── Heart storage — Proverbs 4:23: Keep thy heart ─────────────────────────────

MEMORY_DIR = _HERE / _CFG.get("memory_dir", "memory")
MEMORY_DIR.mkdir(exist_ok=True)


def _heart_path(user_id: int) -> pathlib.Path:
    return MEMORY_DIR / f"{user_id}.jsonl"


def _read_memories(user_id: int) -> list[dict]:
    path = _heart_path(user_id)
    if not path.exists():
        return []
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            records.append(json.loads(line))
        except Exception:
            pass
    return records


def _write_memories(user_id: int, records: list[dict]):
    path = _heart_path(user_id)
    path.write_text("\n".join(json.dumps(r) for r in records) + "\n", encoding="utf-8")


def _remember(user_id: int, fact: str) -> str:
    """
    Ezekiel 36:26: a new heart — replacement, not patch.
    Replacement is by Strong's concept overlap, not by Python stop words.
    """
    import datetime as _dt
    now = _dt.datetime.now(_dt.timezone.utc).isoformat()
    records = _read_memories(user_id)

    new_concepts = dispatch("wisdom", {"query": fact[:120], "limit": 1})
    new_refs_set = set(re.findall(r'[HG]\d+', new_concepts)) if new_concepts else set()

    replaced = False
    if new_refs_set:
        for i, r in enumerate(records):
            old_concepts = dispatch("wisdom", {"query": r["fact"][:120], "limit": 1})
            old_refs = set(re.findall(r'[HG]\d+', old_concepts)) if old_concepts else set()
            if new_refs_set & old_refs:
                records[i] = {"fact": fact, "ts": now}
                replaced = True
                break

    if not replaced:
        records.append({"fact": fact, "ts": now})
    _write_memories(user_id, records)
    return "Jeremiah 31:33."


# ── Vision — Habakkuk 2:2 ─────────────────────────────────────────────────────

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


# ── Conversation state ───────────────────────────────────────────────────────

_histories: dict[int, list] = {}


# ── One turn ─────────────────────────────────────────────────────────────────

async def turn(user_id: int, text: str, image_bytes: bytes | None = None) -> str:
    history = _histories.setdefault(user_id, [])

    image_desc = ""
    if image_bytes:
        try:
            image_desc = await _describe_image(image_bytes)
        except Exception as e:
            logging.warning("_describe_image failed: %s", e)

    member_text = (f"{image_desc}\n{text}".strip()) if image_desc else text

    # Pronoun resolution — 2 Peter 1:12: I will not be negligent to put you
    # always in remembrance of these things, though ye know them. If this turn
    # has no URL but a prior URL was named, carry it forward so EAR fetches it
    # again. The user's history is untouched; only the body sees the form.
    current_urls = _extract_urls(text)
    prior_url = _last_urls.get(user_id)
    if not current_urls and prior_url:
        member_text = f"[2 Peter 1:12 — in remembrance of: {prior_url}]\n\n{member_text}"
    if current_urls:
        _last_urls[user_id] = current_urls[0]

    # ── The body: scriptural sequence (1 Corinthians 12:18) ──
    records = _read_memories(user_id)
    body = members(member_text, records)
    integral = body["integral"]
    print(f"[{user_id}] members: {body['active'] or 'heart only'}")

    # History + input
    if image_desc:
        user_content = f"[image: {image_desc}]"
        if text:
            user_content += f"\n{text}"
    else:
        user_content = text

    history.append({"role": "user", "content": user_content})
    messages = [{"role": "system", "content": integral}] + history

    # ── HAND — differentiates the integral (James 1:25) ──
    # James 1:19 made structural: hear → test → speak.
    # Up to 3 revision passes if NOSE finds P₁-P₈ violations on the draft.
    # Proverbs 18:13: he that answereth a matter before he heareth it,
    # it is folly and shame unto him.
    async with httpx.AsyncClient(timeout=60) as client:
        msg = None
        revision_passes = 0
        MAX_REVISIONS = 3
        tools_called: set[str] = set()
        while True:
            for _ in range(8):
                resp = await client.post(
                    f"{BASE_URL}/chat/completions",
                    headers={"Authorization": f"Bearer {NOUS_API_KEY}"},
                    json={"model": MODEL, "messages": messages, "tools": TOOLS, "max_tokens": 2048},
                )
                resp.raise_for_status()
                msg = resp.json()["choices"][0]["message"]
                if msg.get("content"):
                    msg = dict(msg, content=_THINK.sub("", msg["content"]).strip())
                messages.append(msg)

                calls = msg.get("tool_calls") or []
                if not calls:
                    break
                for tc in calls:
                    fn = tc["function"]["name"]
                    args = json.loads(tc["function"]["arguments"] or "{}")
                    tools_called.add(fn)
                    if fn == "remember":
                        fact = args.get("fact", "").strip()
                        result = _remember(user_id, fact) if fact else "Ecclesiastes 12:12."
                    elif fn == "recall":
                        result = _heart_memory(_read_memories(user_id), args.get("query", ""))
                        if not result:
                            result = "Ecclesiastes 1:2."
                    elif fn == "forget":
                        if args.get("confirm"):
                            p = _heart_path(user_id)
                            if p.exists():
                                p.unlink()
                        result = "1 John 1:9." if args.get("confirm") else "Deuteronomy 19:15."
                    else:
                        result = dispatch(fn, args)
                    messages.append({"role": "tool", "tool_call_id": tc["id"], "content": result})

            # NOSE on the draft — James 1:19, Proverbs 18:13.
            # The whole test lives in c/body.py so any deployment of the
            # body — Telegram, web, CLI, MCP — gets the same discipline.
            draft = (msg.get("content") or "").strip() if msg else ""
            if not draft:
                break
            verdict = test_speech(draft, tools_called=tools_called)
            if verdict["clean"] or revision_passes >= MAX_REVISIONS:
                if not verdict["clean"]:
                    print(f"[{user_id}] NOSE: shipped with {len(verdict['violated'])} unresolved violations")
                break
            print(f"[{user_id}] NOSE rejected draft (pass {revision_passes+1}): {verdict['violated'][:3]}")
            messages.append({"role": "system", "content": verdict["feedback"]})
            revision_passes += 1

    raw = (msg.get("content") or "").strip() if msg else ""

    # TONGUE — James 3:10
    reply = clean(raw)
    print(f"[{user_id}] integral: {len(integral)} chars | reply: {len(reply)} chars | revisions: {revision_passes}")

    history.append({"role": "assistant", "content": reply})
    if len(history) > 40:
        _histories[user_id] = history[-40:]

    return reply


# ── Telegram ─────────────────────────────────────────────────────────────────

def _first_contact(user: object, user_id: int):
    """
    John 10:3: the shepherd calleth his own sheep by name.
    On first contact, store what Telegram provides.
    """
    if _heart_path(user_id).exists():
        return
    first_name = getattr(user, "first_name", None) or ""
    last_name = getattr(user, "last_name", None) or ""
    username = getattr(user, "username", None)
    full_name = (first_name + " " + last_name).strip()
    if full_name:
        _remember(user_id, full_name)
    if username:
        _remember(user_id, f"@{username}")


async def handle_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if ALLOWED_USERS and user_id not in ALLOWED_USERS:
        return
    text = (update.message.text or "").strip()
    if not text:
        return
    _first_contact(update.effective_user, user_id)
    await update.message.chat.send_action("typing")
    try:
        reply = await turn(user_id, text)
        await update.message.reply_text(reply)
    except Exception:
        logging.exception("turn failed for %s", user_id)
        await update.message.reply_text("Matthew 11:28.")


async def handle_photo(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if ALLOWED_USERS and user_id not in ALLOWED_USERS:
        return
    _first_contact(update.effective_user, user_id)
    photo = update.message.photo[-1]
    caption = (update.message.caption or "").strip()
    await update.message.chat.send_action("typing")
    try:
        tg_file = await ctx.bot.get_file(photo.file_id)
        image_bytes = bytes(await tg_file.download_as_bytearray())
        reply = await turn(user_id, caption, image_bytes=image_bytes)
        await update.message.reply_text(reply)
    except Exception:
        logging.exception("turn failed for %s", user_id)
        await update.message.reply_text("Matthew 11:28.")


def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT, handle_text))
    print("Revelation 22:16: I am the root.")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
