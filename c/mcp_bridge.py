"""
mcp_bridge.py — dynamic tool discovery via MCP servers.

1 Corinthians 12:14 — the body is not one member, but many.

External MCP servers can contribute tools to the Hand. The bridge
connects to servers defined in config, discovers their tools, and
dispatches calls. The Hand's built-in tools (from body.py) always
take priority — external tools extend, they don't override.

Usage:
    bridge = MCPBridge()
    await bridge.connect({"name": "my-server", "command": "python", "args": ["-m", "my.server"]})
    tools = bridge.list_tools()       # OpenAI-format tool schemas
    result = bridge.call("tool_name", {"arg": "value"})
    await bridge.close()
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class MCPBridge:
    """
    Lightweight MCP client bridge for the Hand.

    Connects to external MCP servers via stdio, discovers tools,
    and dispatches calls. Thread-safe via asyncio.
    """

    def __init__(self):
        self._servers: dict[str, dict] = {}  # name -> {client, session, tools}
        self._tools: dict[str, str] = {}     # tool_name -> server_name

    async def connect(self, server_config: dict) -> None:
        """
        Connect to an MCP server.

        server_config: {
            "name": str,
            "command": str,         # e.g. "python"
            "args": list[str],      # e.g. ["-m", "c.server"]
            "env": dict (optional),
        }
        """
        name = server_config["name"]
        command = server_config["command"]
        args = server_config.get("args", [])
        env = server_config.get("env")

        try:
            from mcp.client.stdio import stdio_client, StdioServerParameters
            from mcp import ClientSession

            params = StdioServerParameters(
                command=command,
                args=args,
                env=env,
            )

            # Create the stdio connection
            read, write = await asyncio.wait_for(
                stdio_client(params).__aenter__(),
                timeout=30,
            )
            session = ClientSession(read, write)
            await asyncio.wait_for(
                session.__aenter__(),
                timeout=15,
            )
            init_result = await asyncio.wait_for(
                session.initialize(),
                timeout=15,
            )

            # Discover tools
            tools_result = await session.list_tools()
            tool_schemas = []
            for tool in tools_result.tools:
                schema = {
                    "type": "function",
                    "function": {
                        "name": f"mcp_{name}_{tool.name}",
                        "description": tool.description or "",
                        "parameters": tool.inputSchema or {"type": "object", "properties": {}},
                    },
                }
                tool_schemas.append(schema)
                self._tools[f"mcp_{name}_{tool.name}"] = name

            instructions = getattr(init_result, "instructions", "") or ""

            self._servers[name] = {
                "session": session,
                "tools": tool_schemas,
                "instructions": instructions,
            }

            logger.info(
                "MCP %s: connected, %d tools, instructions: %d chars",
                name, len(tool_schemas), len(instructions),
            )

        except Exception as e:
            logger.error("MCP %s: connection failed: %s", name, e)

    def list_tools(self) -> list[dict]:
        """Return all discovered MCP tool schemas in OpenAI format."""
        tools = []
        for srv in self._servers.values():
            tools.extend(srv["tools"])
        return tools

    def get_instructions(self) -> str:
        """Return concatenated instructions from all connected MCP servers."""
        parts = [s["instructions"] for s in self._servers.values() if s["instructions"]]
        return "\n\n".join(parts)

    def is_mcp_tool(self, name: str) -> bool:
        """Is this tool name an MCP tool?"""
        return name in self._tools

    async def call(self, tool_name: str, args: dict) -> str:
        """
        Dispatch a tool call to the appropriate MCP server.
        Returns the result text.
        """
        server_name = self._tools.get(tool_name)
        if not server_name or server_name not in self._servers:
            return f"Unknown MCP tool: {tool_name}"

        session = self._servers[server_name]["session"]
        # Strip the mcp_{server}_ prefix to get the real tool name
        prefix = f"mcp_{server_name}_"
        real_name = tool_name[len(prefix):] if tool_name.startswith(prefix) else tool_name

        try:
            result = await session.call_tool(real_name, args)
            # Extract text content from result
            parts = []
            for content in result.content:
                if hasattr(content, "text"):
                    parts.append(content.text)
            return "\n".join(parts) or "No result."
        except Exception as e:
            logger.error("MCP %s.%s error: %s", server_name, real_name, e)
            return f"MCP tool error: {e}"

    async def close(self) -> None:
        """Disconnect all MCP servers."""
        for name, srv in self._servers.items():
            try:
                await srv["session"].__aexit__(None, None, None)
            except Exception:
                pass
            logger.info("MCP %s: disconnected", name)
        self._servers.clear()
        self._tools.clear()
