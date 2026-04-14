"""
OpenAI-compatible adapter with Hermes-4 extensions.

Works with ANY model served via an OpenAI-compatible API (Nous Portal,
OpenRouter, vLLM, etc.): MiMo, Hermes, Qwen, Llama, Mistral, etc.
Standard models use the native structured tool_calls field.

For Hermes-4 specifically: Hermes uses <tool_call>...</tool_call> XML
tags inside the content field instead of structured tool_calls. The
adapter auto-detects Hermes by model name and enables XML parsing +
format instruction only for those models. All other models get standard
OpenAI behavior with no XML instruction injected.
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
import uuid

import httpx

from c.adapters.base import Adapter

logger = logging.getLogger(__name__)

# ── Redaction (Proverbs 11:13) ────────────────────────────────────────────
# A talebearer revealeth secrets: but he that is of a faithful spirit
# concealeth the matter. Strip credentials from error output before
# they reach the scroll or chain log.
_CREDENTIAL_RE = re.compile(
    r"(sk-[a-zA-Z0-9]{10,}|"              # API keys
    r"Bearer\s+[a-zA-Z0-9._\-]{20,}|"     # Bearer tokens
    r"token[=:]\s*['\"]?[a-zA-Z0-9._\-]{20,}|"  # token=...
    r"key[=:]\s*['\"]?[a-zA-Z0-9._\-]{20,})",    # key=...
    re.I,
)


def redact(text: str) -> str:
    """Strip credentials from error text. Proverbs 11:13."""
    return _CREDENTIAL_RE.sub("[REDACTED]", text)


_TOOL_CALL_RE = re.compile(
    r"<tool_call>\s*(.*?)\s*</tool_call>|<tool_call>\s*(.*)",
    re.DOTALL,
)

# This instruction describes the FORMAT for tool calls only — not WHEN
# to call them. The "when" is the body's job (kernel.md, _head, NOSE).
# Earlier versions of this instruction included Luke 19:5 priming
# ("when sharing a personal fact about the user, call remember") and the
# model interpreted that as a standing imperative, calling remember on
# every turn and INVENTING facts to satisfy the rule. Romans 7:8: sin,
# taking occasion by the commandment, wrought in me all manner of
# concupiscence. The format spec is descriptive. The action triggers
# stay reactive (NOSE conviction), not proactive (always call X).
_INSTRUCTION = (
    "\n\n"
    "Tool-call format: when you decide to call a tool, emit exactly one "
    "block per call, using this XML format:\n"
    "<tool_call>\n"
    "{\"name\": \"<tool-name>\", \"arguments\": {<args>}}\n"
    "</tool_call>\n"
    "The JSON inside must be a single object with \"name\" and "
    "\"arguments\" fields. Do not use <tools> as a wrapper. Tool results "
    "will appear in the next message. Whether and when to call a tool "
    "is your judgment from C — this instruction only tells you the "
    "syntax, not the occasion."
)


class HermesAdapter(Adapter):
    def __init__(
        self,
        api_key: str,
        model: str = "Hermes-4-70B",
        base_url: str = "https://inference-api.nousresearch.com/v1",
        timeout: float = 60.0,
        max_retries: int = 3,
    ):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        # Hermes is fast (single-turn ~5s). Non-Hermes models (MiMo etc.)
        # take 10-40s per call; with tool loops + NOSE retries a single turn
        # can chain 5-8 calls. 120s keeps the connection alive.
        self.timeout = timeout if self._is_hermes() else max(timeout, 120.0)
        self.max_retries = max_retries
        # Connection pool — reuse TCP connections across calls within a turn.
        # Creating a new client per call wastes the TLS handshake.
        self._client: httpx.AsyncClient | None = None

    def describe(self) -> str:
        return f"HermesAdapter(model={self.model})"

    def _is_hermes(self) -> bool:
        return "hermes" in self.model.lower()

    def system_instruction(self) -> str:
        # Hermes-4 needs explicit XML tool-call format instruction.
        # Other models on the Nous API (MiMo, etc.) use standard OpenAI
        # structured tool calls and do NOT need this — injecting it
        # confuses them into emitting XML tags instead of using the
        # native tool_calls field.
        if self._is_hermes():
            return _INSTRUCTION
        return ""

    def parse_tool_calls(self, content: str) -> tuple[str, list[dict]]:
        # Only parse <tool_call> XML for Hermes models. Other models
        # return structured tool_calls from the API directly.
        if not self._is_hermes():
            return content, []
        if not content or "<tool_call>" not in content:
            return content, []
        matches = _TOOL_CALL_RE.findall(content)
        if not matches:
            return content, []
        calls = []
        for closed, unclosed in matches:
            raw = (closed or unclosed).strip()
            if not raw:
                continue
            try:
                tc = json.loads(raw)
            except Exception:
                # Hermes JSON sometimes uses single quotes — last-resort fallback.
                try:
                    tc = json.loads(raw.replace("'", '"'))
                except Exception:
                    continue
            name = tc.get("name") if isinstance(tc, dict) else None
            if not name:
                continue
            args = tc.get("arguments", {}) if isinstance(tc, dict) else {}
            calls.append({
                "id": f"call_{uuid.uuid4().hex[:8]}",
                "type": "function",
                "function": {
                    "name": name,
                    "arguments": (
                        json.dumps(args, ensure_ascii=False)
                        if not isinstance(args, str)
                        else args
                    ),
                },
            })
        if not calls:
            return content, []
        cleaned = re.sub(
            r"<tool_call>.*?(?:</tool_call>|$)", "", content, flags=re.DOTALL
        ).strip()
        return cleaned, calls

    async def _get_client(self) -> httpx.AsyncClient:
        """Reuse a persistent connection pool. Proverbs 21:5 — diligent."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    async def complete(
        self,
        messages: list[dict],
        tools: list[dict],
        max_tokens: int = 2048,
    ) -> dict:
        """
        Call the API with retry + exponential backoff.

        Proverbs 24:16 — a just man falleth seven times, and riseth
        up again. Transient failures (429, 5xx, network) are retried;
        client errors (4xx except 429) are not.
        """
        client = await self._get_client()
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
        }
        if tools:
            payload["tools"] = tools

        last_err = None
        for attempt in range(self.max_retries + 1):
            try:
                resp = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json=payload,
                )
                resp.raise_for_status()
                return resp.json()["choices"][0]["message"]
            except httpx.HTTPStatusError as e:
                last_err = e
                code = e.response.status_code
                # Retry on 429 (rate limit) and 5xx (server error)
                if code == 429 or code >= 500:
                    delay = min(2 ** attempt, 30)
                    logger.warning(
                        "API %d on attempt %d/%d, retrying in %ds",
                        code, attempt + 1, self.max_retries + 1, delay,
                    )
                    await asyncio.sleep(delay)
                    continue
                # Non-retryable client error — redact and raise
                raise type(e)(redact(str(e)), request=e.request, response=e.response) from None
            except (httpx.ConnectError, httpx.ReadTimeout, httpx.WriteTimeout) as e:
                last_err = e
                delay = min(2 ** attempt, 30)
                logger.warning(
                    "Network error on attempt %d/%d: %s, retrying in %ds",
                    attempt + 1, self.max_retries + 1, type(e).__name__, delay,
                )
                # Reset client on network error
                self._client = None
                client = await self._get_client()
                await asyncio.sleep(delay)
                continue

        raise last_err  # exhausted retries
