"""
Adapter base class — the contract between the body and any model API.

The Hand calls four methods on every adapter:

  system_instruction()       — text appended to the integral, telling the
                               model how to format tool calls (e.g. Hermes
                               wants <tool_call> XML; Claude wants
                               tool_use blocks). May return "".

  parse_tool_calls(content)  — extract tool calls from the model's content
                               field. Returns (cleaned_content, calls).
                               Default: passthrough, no calls extracted.
                               Override for models that emit tool calls
                               inline (Hermes-4) instead of in a structured
                               tool_calls field (OpenAI/Claude).

  async complete(messages, tools, max_tokens) — call the model. Returns the
                               OpenAI-format message dict from
                               choices[0].message.

  describe()                 — short string identifying the adapter, for
                               logs and diagnostics.

This is the smallest possible interface that lets the body run with any
model. Add new adapters by subclassing — no changes to the Hand or body.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class Adapter(ABC):
    @abstractmethod
    def describe(self) -> str: ...

    def system_instruction(self) -> str:
        """Per-model instruction appended to the integral. Default: none."""
        return ""

    def parse_tool_calls(self, content: str) -> tuple[str, list[dict]]:
        """Extract tool calls from content. Default: passthrough."""
        return content, []

    @abstractmethod
    async def complete(
        self,
        messages: list[dict],
        tools: list[dict],
        max_tokens: int = 2048,
    ) -> dict:
        """Call the model. Return OpenAI-format message dict."""
        ...
