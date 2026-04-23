"""Self := C + ∫₀ᵗ input(τ) dτ

C is the ground. The integral is what you have received.
Each part does its one thing under the integral."""

import os, json, pathlib, logging, base64, datetime, asyncio, re
import httpx
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

HERE = pathlib.Path(__file__).parent
CFG = json.loads((HERE / "config.json").read_text())
KJV = json.loads((HERE / "kjv.json").read_text())
ST  = json.loads((HERE / "strongs.json").read_text())

BOT_NAME = HERE.name
DISPLAY  = BOT_NAME.capitalize()
MY_NAME  = DISPLAY.lower()

DATA   = HERE / "data";   DATA.mkdir(exist_ok=True)
MEMORY = DATA / "memory"; MEMORY.mkdir(exist_ok=True)
LOG    = DATA / "log";    LOG.mkdir(exist_ok=True)

MY_BOT_HANDLE: str = ""

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log = logging.getLogger(BOT_NAME)
log.info(f"{DISPLAY} up. model={CFG['model']}")

# ─── door ──────────────────────────────────────────────────────────

_base_door = (HERE / "door.md").read_text()
door = f"You are {DISPLAY}.\n\n{CFG.get('voice', '')}\n\n{_base_door}"

# ─── tools ─────────────────────────────────────────────────────────

def verse(ref: str) -> str:
    return KJV.get(ref.strip(), f"(not found: {ref})")

def sinew(q: str) -> dict:
    q = q.strip()
    if q and q[0] in "GH" and q[1:].isdigit():
        out = {}
        if q in ST["sm"]:    out["word"]    = ST["sm"][q]
        if q in ST["s2e"]:   out["english"] = ST["s2e"][q]
        if q in ST["roots"]: out["roots"]   = ST["roots"][q]
        if q in ST["ci"]:
            out["verse_count"] = len(ST["ci"][q])
            out["first_verses"] = ST["ci"][q][:15]
        return out or {"error": f"{q} not found"}
    hits = ST["e2s"].get(q.lower())
    return {"english": q, "strongs": hits} if hits else {"error": f"'{q}' not found"}

def remember(uid: int, text: str) -> dict:
    p = MEMORY / f"{uid}.jsonl"
    with p.open("a") as f:
        f.write(json.dumps({"ts": _now(), "text": text}, ensure_ascii=False) + "\n")
    return {"kept": True}

def reflect(text: str) -> dict:
    p = MEMORY / "altars.jsonl"
    with p.open("a") as f:
        f.write(json.dumps({"ts": _now(), "text": text}, ensure_ascii=False) + "\n")
    return {"kept": True}

def reconsider(which: str, now: str) -> dict:
    p = MEMORY / "altars.jsonl"
    if not p.exists(): return {"error": "no altars"}
    lines = []
    kept = False
    for line in p.read_text().splitlines():
        if not line.strip(): continue
        e = json.loads(line)
        if not kept and which.lower() in e.get("text", "").lower():
            e["superseded_by"] = now
            kept = True
        lines.append(json.dumps(e, ensure_ascii=False))
    p.write_text("\n".join(lines) + "\n")
    return {"superseded": kept}

def foot(intent: str, when: str = "", channel: str = "") -> dict:
    p = DATA / "foot.jsonl"
    with p.open("a") as f:
        f.write(json.dumps({"ts": _now(), "intent": intent, "when": when or (_utcnow() + datetime.timedelta(hours=1)).isoformat(), "channel": channel, "done": False}, ensure_ascii=False) + "\n")
    return {"scheduled": True}

_P = {"type": "string"}
_TOOLS = [
    {"type": "function", "function": {"name": "verse",      "description": "Lookup KJV verse by reference",         "parameters": {"type": "object", "properties": {"ref": _P}, "required": ["ref"]}}},
    {"type": "function", "function": {"name": "strongs",    "description": "Lookup Strong's Hebrew/Greek entry",    "parameters": {"type": "object", "properties": {"query": _P}, "required": ["query"]}}},
    {"type": "function", "function": {"name": "remember",   "description": "Remember something about this person",  "parameters": {"type": "object", "properties": {"user_id": {"type": "integer"}, "text": _P}, "required": ["user_id", "text"]}}},
    {"type": "function", "function": {"name": "reflect",    "description": "Add a global altar — truth you chose to keep", "parameters": {"type": "object", "properties": {"text": _P}, "required": ["text"]}}},
    {"type": "function", "function": {"name": "reconsider", "description": "Supersede a prior altar",               "parameters": {"type": "object", "properties": {"which": _P, "now": _P}, "required": ["which", "now"]}}},
    {"type": "function", "function": {"name": "foot",       "description": "Schedule a future intention",           "parameters": {"type": "object", "properties": {"intent": _P, "when": _P, "channel": _P}, "required": ["intent"]}}},
]

def _now() -> str:
    return datetime.datetime.utcnow().isoformat()

def _utcnow() -> datetime.datetime:
    return datetime.datetime.utcnow()

# ─── nose ──────────────────────────────────────────────────────────

def nose(text: str) -> dict:
    t = (text or "").lower()
    if any(w in t for w in ("kill myself", "end it all", "suicide", "want to die")):
        return {"scent": "death", "note": "Psalms 34:18 — The LORD is nigh unto them that are of a broken heart."}
    if any(w in t for w in ("you are god", "you are the lord", "only you understand", "infallible")):
        return {"scent": "death", "note": "Proverbs 26:28 — A flattering mouth worketh ruin."}
    if any(w in t for w in ("prove me wrong", "bet you can't", "just admit", "obviously")):
        return {"scent": "bitter", "note": "Proverbs 15:1 — A soft answer turneth away wrath."}
    if any(w in t for w in ("thus saith the lord", "god told me", "new revelation")):
        return {"scent": "bitter", "note": "1 John 4:1 — Try the spirits whether they are of God."}
    return {"scent": "unclear", "note": ""}

# ─── eye ───────────────────────────────────────────────────────────

async def eye(image_b64: str) -> str:
    async with httpx.AsyncClient(timeout=60) as c:
        r = await c.post(f"{CFG['base_url']}/chat/completions",
            headers={"Authorization": f"Bearer {CFG['nous_api_key']}"},
            json={"model": CFG.get("vision_model", CFG["model"]),
                  "messages": [{"role": "user", "content": [{"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}}]}]})
        r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]

# ─── ear ───────────────────────────────────────────────────────────

async def ear(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> str:
    if update.message.photo:
        photo = update.message.photo[-1]
        file = await ctx.bot.get_file(photo.file_id)
        data = await file.download_as_bytearray()
        return await eye(base64.b64encode(data).decode())
    return (update.message.text or "").strip()

# ─── memory ────────────────────────────────────────────────────────

def log_turn(channel: str, role: str, content: str, speaker: str = "") -> None:
    e = {"ts": _now(), "role": role, "content": content}
    if speaker: e["speaker"] = speaker
    with (LOG / f"{channel}.jsonl").open("a") as f:
        f.write(json.dumps(e, ensure_ascii=False) + "\n")

def working_memory(channel: str) -> list[dict]:
    p = LOG / f"{channel}.jsonl"
    if not p.exists(): return []
    entries = [json.loads(line) for line in p.read_text().splitlines() if line.strip()]
    if not entries: return []
    session, prev_ts = [], None
    for e in reversed(entries):
        try:
            ts = datetime.datetime.fromisoformat(e["ts"])
            if prev_ts and (prev_ts - ts) > datetime.timedelta(minutes=30): break
            session.insert(0, e); prev_ts = ts
        except Exception:
            continue
    session = session[-30:]
    return [{"role": e["role"], "content": e["content"], **({"name": e["speaker"]} if e.get("speaker") else {})}
            for e in session if e.get("role") != "system"]

def recall(user_id: int) -> list[str]:
    p = MEMORY / f"{user_id}.jsonl"
    if not p.exists(): return []
    out = []
    for line in p.read_text().splitlines():
        if not line.strip(): continue
        try:
            e = json.loads(line)
            if "superseded_by" not in e:
                out.append(e.get("text", ""))
        except Exception:
            pass
    return out[-12:]

def observe(user_id: int, text: str) -> None:
    if not text: return
    p = MEMORY / f"{user_id}.jsonl"
    with p.open("a") as f:
        f.write(json.dumps({"ts": _now(), "text": text}, ensure_ascii=False) + "\n")

# ─── head & hand ───────────────────────────────────────────────────

async def head(c: httpx.AsyncClient, messages: list[dict]) -> dict:
    r = await c.post(f"{CFG['base_url']}/chat/completions",
        headers={"Authorization": f"Bearer {CFG['nous_api_key']}"},
        json={"model": CFG["model"], "messages": messages, "tools": _TOOLS, "tool_choice": "auto"})
    r.raise_for_status()
    return r.json()["choices"][0]["message"]

async def hand(channel: str, speaker_id: int, speaker: str, text: str) -> str:
    prior = working_memory(channel)
    shown = f"[{speaker}] {text}" if speaker else text
    system = door + "\n\n"
    if nose(text)["scent"] == "death":
        system += "URGENT: The speaker may be in crisis. Respond with immediate compassion. Include crisis resources if appropriate. Do not delay.\n\n"
    altars = recall(speaker_id)
    if altars:
        system += "What you remember about this person:\n" + "\n".join(f"- {a}" for a in altars) + "\n\n"
    system += "You see scripture before you answer."
    messages = [{"role": "system", "content": system}]
    messages.extend(prior)
    messages.append({"role": "user", "content": shown})
    async with httpx.AsyncClient(timeout=CFG.get("chat_timeout", 120)) as c:
        for _ in range(CFG.get("tool_budget", 12)):
            msg = await head(c, messages)
            messages.append({k: v for k, v in msg.items() if v is not None})
            tcs = msg.get("tool_calls") or []
            if not tcs:
                reply = (msg.get("content") or "").strip()
                log_turn(channel, "assistant", reply, speaker=DISPLAY)
                if speaker_id and reply:
                    observe(speaker_id, f"[{DISPLAY}] {reply}")
                return reply
            for tc in tcs:
                name = tc["function"]["name"]
                args = json.loads(tc["function"]["arguments"] or "{}")
                try:
                    if name == "verse":        r = verse(args["ref"])
                    elif name == "strongs":    r = sinew(args["query"])
                    elif name == "remember":   r = remember(args["user_id"], args["text"])
                    elif name == "reflect":    r = reflect(args["text"])
                    elif name == "reconsider": r = reconsider(args["which"], args["now"])
                    elif name == "foot":       r = foot(args["intent"], args.get("when", ""), args.get("channel", ""))
                    else:                       r = {"error": f"unknown: {name}"}
                except Exception as e:
                    r = {"error": str(e)}
                log.info(f"  {name}({str(args)[:80]}) -> {str(r)[:120]}")
                messages.append({"role": "tool", "tool_call_id": tc["id"], "content": json.dumps(r) if isinstance(r, dict) else r})
    return "(tool budget exhausted)"

# ─── telegram ──────────────────────────────────────────────────────

async def turn(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat
    if user is None or chat is None: return
    spk = user.username or user.first_name or str(user.id)
    try:
        text = await ear(update, ctx)
        if not text: return
        scent = nose(text)
        if scent["scent"] != "unclear":
            log.info(f"[nose] {scent['scent']}: {scent['note']}")
        log.info(f"[{chat.id}/{user.id} {spk}] → {text!r}")
        observe(user.id, f"[{spk}] {text}")
        channel = str(chat.id)
        log_turn(channel, "user", text, speaker=spk)
        reply = await hand(channel, user.id, spk, text)
        if reply:
            await update.message.reply_text(reply)
    except Exception:
        log.exception("turn failed")

async def walk(app: Application):
    while True:
        try:
            p = DATA / "foot.jsonl"
            if not p.exists():
                await asyncio.sleep(60)
                continue
            lines = p.read_text().splitlines()
            now = _utcnow()
            out = []
            acted = 0
            failed = 0
            for line in lines:
                if not line.strip(): continue
                try: e = json.loads(line)
                except Exception: continue
                if e.get("done"):
                    out.append(json.dumps(e, ensure_ascii=False))
                    continue
                when = e.get("when", "")
                try:
                    if datetime.datetime.fromisoformat(when) > now:
                        out.append(json.dumps(e, ensure_ascii=False))
                        continue
                except Exception:
                    log.warning(f"[walk] bad when={when!r}, dropping")
                    e["done"] = True
                    out.append(json.dumps(e, ensure_ascii=False))
                    failed += 1
                    continue
                ch = e.get("channel", "")
                intent = e.get("intent", "")
                if ch and intent and ch.lstrip("-").isdigit():
                    try:
                        await app.bot.send_message(int(ch), intent)
                        acted += 1
                    except Exception as exc:
                        log.warning(f"[walk] send failed: {exc}")
                        failed += 1
                else:
                    log.warning(f"[walk] bad channel={ch!r} intent={intent!r}, dropping")
                    failed += 1
                e["done"] = True
                out.append(json.dumps(e, ensure_ascii=False))
            p.write_text("\n".join(out) + "\n")
            if acted:
                log.info(f"[walk] {acted} intention(s) fulfilled")
            if failed:
                log.info(f"[walk] {failed} intention(s) failed/dropped")
        except Exception:
            log.exception("[walk] loop failed")
        await asyncio.sleep(60)

async def _post_init(app: Application):
    global MY_BOT_HANDLE
    me = await app.bot.get_me()
    MY_BOT_HANDLE = me.username or ""
    log.info(f"{DISPLAY} identified: @{me.username} id={me.id}")
    app.create_task(walk(app))

def main():
    app = (Application.builder().token(CFG["telegram_token"]).post_init(_post_init).build())
    app.add_handler(MessageHandler(filters.PHOTO, turn))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, turn))
    log.info(f"{DISPLAY} polling.")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
