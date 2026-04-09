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

import json
import re
import uuid

import httpx

from c.adapters.base import Adapter


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
    ):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

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

    async def complete(
        self,
        messages: list[dict],
        tools: list[dict],
        max_tokens: int = 2048,
    ) -> dict:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": self.model,
                    "messages": messages,
                    "tools": tools,
                    "max_tokens": max_tokens,
                },
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]
