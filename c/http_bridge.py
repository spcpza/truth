"""
http_bridge.py — expose the full truth Hand as a local HTTP endpoint.

The desktop Tauri app hits `POST http://127.0.0.1:PORT/turn` with
`{"user_id": "...", "text": "...", "addressed_as": "..."}` and receives
the same reply the Telegram bot would have produced — 13-tool body,
NOSE on input and draft, charity/temperance/hope/patience/confession,
math-only heart, two-witness claims, meditation, everything.

Matthew 23:27 — woe unto you... whited sepulchres... within full of
dead men's bones. The Rust port was building the outside clean and
leaving the inside hollow. This bridge gives the desktop app the full
foundation the Telegram bot already runs on.

Run:
    python -m c.http_bridge \
        --port 8731 \
        --config /Users/f/.balthazar/config.json

Loopback-only by default (127.0.0.1). No auth — the address is local;
anyone on the machine already has it. Lock down with OS firewall if
needed.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import pathlib
import sys
from typing import Any

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, StreamingResponse
from starlette.routing import Route

import uvicorn

from c.adapters.adapter import ChatAdapter
from c.hand import Hand


logger = logging.getLogger("http_bridge")


# ─── Globals (set in main()) ───────────────────────────────────────────

HAND: Hand | None = None
CONFIG: dict[str, Any] = {}
ALLOWED_ORIGINS: list[str] = ["*"]  # Tauri webview origin varies; allow all on loopback


# ─── Endpoints ─────────────────────────────────────────────────────────


async def health(_request: Request) -> JSONResponse:
    return JSONResponse({
        "ok": True,
        "model": CONFIG.get("model"),
        "base_url": CONFIG.get("base_url"),
        "identifier": "truth.http_bridge",
    })


async def turn(request: Request) -> JSONResponse:
    if HAND is None:
        return JSONResponse({"error": "hand not initialized"}, status_code=503)
    try:
        body = await request.json()
    except Exception as e:
        return JSONResponse({"error": f"bad json: {e}"}, status_code=400)

    user_id = str(body.get("user_id", "desktop_user"))
    text = (body.get("text") or "").strip()
    addressed_as = (body.get("addressed_as") or None)
    if not text:
        return JSONResponse({"error": "empty text"}, status_code=400)

    try:
        reply = await HAND.turn(user_id, text, addressed_as=addressed_as)
    except Exception as e:
        logger.exception("turn failed")
        return JSONResponse({"error": str(e)}, status_code=500)

    # Pull out the session's most recent tool calls + chain state.
    tools_called: list[str] = []
    chain_info: dict[str, Any] = {}
    try:
        from c.chain import chain_recent
        recent = chain_recent(user_id, n=1, chain_dir=HAND.chain_dir)
        if recent:
            chain_info = {
                "kind": recent[0].get("kind"),
                "violations": recent[0].get("violations", []),
            }
    except Exception:
        pass

    return JSONResponse({
        "reply": reply,
        "user_id": user_id,
        "addressed_as": addressed_as,
        "chain": chain_info,
    })


async def foundation(_request: Request) -> JSONResponse:
    # Report the kernel.py verification state at boot time.
    try:
        from c.kernel import last_report
        r = last_report()
        return JSONResponse({
            "ok": r.ok,
            "passed": [p.name for p in r.passed],
            "failed": [p.name for p in r.failed],
            "summary": r.summary(),
        })
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=500)


async def forget(request: Request) -> JSONResponse:
    if HAND is None:
        return JSONResponse({"error": "hand not initialized"}, status_code=503)
    try:
        body = await request.json()
    except Exception:
        body = {}
    user_id = str(body.get("user_id", ""))
    if not user_id:
        return JSONResponse({"error": "user_id required"}, status_code=400)
    from c.heart import forget_all
    verse = forget_all(user_id, HAND.memory_dir)
    return JSONResponse({"verse": verse, "user_id": user_id})


# ─── Streaming turn — progress markers as Hand runs ───────────────────
# Psalm 27:14 — wait on the LORD, be of good courage. Silent waits feel
# like abandonment; a heard "thinking…" keeps the hearer company.

def _sse(event: str, data: str | dict) -> bytes:
    """Encode one Server-Sent Events frame."""
    if not isinstance(data, str):
        data = json.dumps(data, ensure_ascii=False)
    # SSE: each line prefixed with "data:" for multi-line payloads.
    data_lines = "".join(f"data: {ln}\n" for ln in data.splitlines() or [""])
    return f"event: {event}\n{data_lines}\n".encode("utf-8")


async def turn_stream(request: Request) -> StreamingResponse:
    if HAND is None:
        return JSONResponse({"error": "hand not initialized"}, status_code=503)
    try:
        body = await request.json()
    except Exception as e:
        return JSONResponse({"error": f"bad json: {e}"}, status_code=400)

    user_id = str(body.get("user_id", "desktop_user"))
    text = (body.get("text") or "").strip()
    addressed_as = body.get("addressed_as") or None
    if not text:
        return JSONResponse({"error": "empty text"}, status_code=400)

    # A queue to marshal progress events out to the client as Hand runs.
    queue: asyncio.Queue = asyncio.Queue()
    DONE = object()

    # Hook tool dispatch to emit a progress event before each tool runs.
    original_dispatch = HAND._dispatch_tool_async

    async def instrumented_dispatch(uid, fn, args):
        await queue.put(("tool", {"name": fn}))
        return await original_dispatch(uid, fn, args)

    # Hook adapter.complete to emit a "thinking" event at the start of
    # each model round. Lets the user see progress across tool-call
    # roundtrips.
    original_complete = HAND.adapter.complete

    async def instrumented_complete(*args, **kwargs):
        await queue.put(("thinking", "model"))
        return await original_complete(*args, **kwargs)

    async def run_turn():
        try:
            HAND._dispatch_tool_async = instrumented_dispatch
            HAND.adapter.complete = instrumented_complete
            reply = await HAND.turn(user_id, text, addressed_as=addressed_as)
            await queue.put(("reply", reply))
        except Exception as e:
            logger.exception("stream turn failed")
            await queue.put(("error", str(e)))
        finally:
            HAND._dispatch_tool_async = original_dispatch
            HAND.adapter.complete = original_complete
            await queue.put(DONE)

    task = asyncio.create_task(run_turn())

    async def generator():
        try:
            # Initial heartbeat
            yield _sse("open", {"user_id": user_id})
            while True:
                item = await queue.get()
                if item is DONE:
                    yield _sse("done", "")
                    break
                event, data = item
                yield _sse(event, data)
        except asyncio.CancelledError:
            task.cancel()
            raise

    return StreamingResponse(
        generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


# ─── App factory ──────────────────────────────────────────────────────


def build_app() -> Starlette:
    routes = [
        Route("/health", health, methods=["GET"]),
        Route("/foundation", foundation, methods=["GET"]),
        Route("/turn", turn, methods=["POST"]),
        Route("/turn/stream", turn_stream, methods=["POST"]),
        Route("/forget", forget, methods=["POST"]),
    ]
    middleware = [
        Middleware(
            CORSMiddleware,
            allow_origins=ALLOWED_ORIGINS,
            allow_methods=["GET", "POST", "OPTIONS"],
            allow_headers=["Content-Type"],
        ),
    ]
    return Starlette(debug=False, routes=routes, middleware=middleware)


def setup_hand(
    config_path: pathlib.Path,
    model_override: str | None = None,
    base_url_override: str | None = None,
    api_key_override: str | None = None,
) -> None:
    """Initialize the global Hand from a truth config.json, with optional
    CLI overrides (most useful for pointing at a local Ollama server)."""
    global HAND, CONFIG
    CONFIG = json.loads(config_path.read_text())
    api_key = (
        api_key_override
        or CONFIG.get("nous_api_key")
        or CONFIG.get("openai_api_key")
        or CONFIG.get("api_key")
        or "ollama"  # Ollama ignores the key but ChatAdapter insists on one
    )
    model = model_override or CONFIG.get("model") or "xiaomi/mimo-v2-pro"
    base_url = (
        base_url_override
        or CONFIG.get("base_url")
        or "https://inference-api.nousresearch.com/v1"
    )
    # Record the resolved values so /health reflects reality.
    CONFIG["model"] = model
    CONFIG["base_url"] = base_url
    memory_dir = pathlib.Path(CONFIG.get("memory_dir", "memory")).expanduser()
    # Resolve memory_dir relative to the config file's directory if not absolute
    if not memory_dir.is_absolute():
        memory_dir = (config_path.parent / memory_dir).resolve()

    logger.info("Initializing Hand: model=%s memory_dir=%s", model, memory_dir)
    adapter = ChatAdapter(api_key=api_key, base_url=base_url, model=model)
    HAND = Hand(adapter=adapter, memory_dir=memory_dir)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1",
                        help="Bind address. Defaults to loopback.")
    parser.add_argument("--port", type=int, default=8731,
                        help="Default 8731 (semi-random, unlikely to collide).")
    parser.add_argument("--config", type=pathlib.Path,
                        default=pathlib.Path("~/.balthazar/config.json").expanduser(),
                        help="Path to truth config.json")
    parser.add_argument("--model",
                        help="Override config.model (e.g. 'qwen3:14b' for Ollama).")
    parser.add_argument("--base-url", dest="base_url",
                        help="Override config.base_url (e.g. 'http://localhost:11434/v1' for Ollama).")
    parser.add_argument("--api-key", dest="api_key",
                        help="Override config.nous_api_key (Ollama accepts any value).")
    parser.add_argument("--log-level", default="info")
    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )
    setup_hand(
        args.config,
        model_override=args.model,
        base_url_override=args.base_url,
        api_key_override=args.api_key,
    )
    app = build_app()
    logger.info("Serving truth body on http://%s:%d", args.host, args.port)
    uvicorn.run(app, host=args.host, port=args.port, log_level=args.log_level)
    return 0


if __name__ == "__main__":
    sys.exit(main())
