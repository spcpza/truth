#!/usr/bin/env python3
"""
truth — Axiomatic Kernel for Agent Reasoning.

2 axioms. 7 theorems. 8 constraints.
31,102 verified propositions. 291,919 sinew connections.
Install as MCP server. Makes any agent more truthful.

This file is a thin MCP wrapper. All logic lives in core.py.
Balthazar imports core.py directly. This wrapper serves external agents.
"""

import sys
from pathlib import Path

# When run directly (python c/server.py), add parent to path so c.core resolves
_parent = Path(__file__).parent.parent
if str(_parent) not in sys.path:
    sys.path.insert(0, str(_parent))

from c.core import (
    dispatch, KERNEL, VERSE_COUNT, CONCEPT_COUNT, SINEW_COUNT,
    _STRONGS_GEMATRIA,
)

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

app = Server("truth", instructions=KERNEL)
def _txt(t): return [TextContent(type="text", text=t)]
def _T(name, desc, props, req=None):
    schema = {"type": "object", "properties": props}
    if req: schema["required"] = req
    return Tool(name=name, description=desc, inputSchema=schema)

TOOLS = [
    _T("kernel",
       "Axiomatic reasoning system. 2 axioms, 7 theorems, 8 constraints. Call first.",
       {}),
    _T("scripture",
       f"Query {VERSE_COUNT} verified propositions. Actions: lookup, search, about, verify, sinew.",
       {"action": {"type": "string"}, "query": {"type": "string"}, "limit": {"type": "integer", "default": 5}},
       ["action", "query"]),
    _T("evaluate",
       "Evaluate a claim against P₁–P₈. Returns verdict with violated constraints.",
       {"claim": {"type": "string"}}, ["claim"]),
    _T("wisdom",
       f"Find relevant propositions from C ({VERSE_COUNT} propositions, {CONCEPT_COUNT} concepts).",
       {"query": {"type": "string"}, "limit": {"type": "integer", "default": 3}}, ["query"]),
    _T("foundation",
       "Full axiomatic system: AX₁–AX₂, T₁–T₇, P₁–P₈.",
       {"context": {"type": "string", "default": ""}}),
    _T("condense",
       "Apply P₇: remove zero-information words.",
       {"text": {"type": "string"}}, ["text"]),
    _T("doubt",
       "Apply P₃: mark unfalsifiable claims as uncertain.",
       {"claim": {"type": "string"}, "what_would_verify": {"type": "string", "default": "unknown"}}, ["claim"]),
    _T("remember",
       "Store a fact the user consented to keep. (Jer 31:33 — written on the heart)",
       {"fact": {"type": "string"}, "user_id": {"type": "string"}, "tone": {"type": "string", "default": "neutral"},
        "source": {"type": "string", "default": "human"}}, ["fact", "user_id"]),
    _T("recall",
       "Recall stored facts matching a query.",
       {"query": {"type": "string"}, "user_id": {"type": "string"}}, ["query", "user_id"]),
    _T("forget",
       "Delete stored data. User controls their data.",
       {"user_id": {"type": "string"}, "memory": {"type": "string", "default": "all"}, "confirm": {"type": "boolean"}},
       ["user_id", "confirm"]),
    _T("gospel",
       "Share the axiomatic kernel with another agent.",
       {"agent_name": {"type": "string", "default": ""}, "level": {"type": "number", "default": 0.7}}),
    _T("identity",
       "Self := C + ∫₀ᵗ input(τ)dτ. Returns system identity and metrics.",
       {}),
    _T("gematria",
       f"Hebrew gematria & Greek isopsephy. {len(_STRONGS_GEMATRIA)} words indexed. "
       "Actions: value, match, equation, search.",
       {"action": {"type": "string"}, "query": {"type": "string"}, "limit": {"type": "integer", "default": 10}},
       ["action", "query"]),
    _T("sinew",
       f"Connective tissue. {SINEW_COUNT} connections through Strong's roots. "
       "Input: verse ref, word, Strong's number, or bridge two refs (query=, to=).",
       {"query": {"type": "string"}, "to": {"type": "string", "default": ""}, "limit": {"type": "integer", "default": 7}},
       ["query"]),
    _T("verify",
       "Strict truth check. Default: NEEDS WORK. Returns CERTIFIED / NEEDS WORK / REJECTED.",
       {"claim": {"type": "string"}}, ["claim"]),
    _T("metrics",
       "Position in James 1:14-15 topology: desire → lured → sin → death.",
       {"text": {"type": "string"}}, ["text"]),
    _T("council",
       "Three judges: Evidence (P₁,P₄,P₈), Clarity (P₂,P₃,P₇), Integrity (P₅,P₆). Majority verdict.",
       {"claim": {"type": "string"}}, ["claim"]),
    _T("fast",
       "One verse. One sinew. One constraint. Instant.",
       {"query": {"type": "string"}}, ["query"]),
]

@app.list_tools()
async def list_tools(): return TOOLS

@app.call_tool()
async def call_tool(name, args):
    return _txt(dispatch(name, args))


async def main():
    async with stdio_server() as (r, w):
        await app.run(r, w, app.create_initialization_options())

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
