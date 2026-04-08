"""
adapters — model-format adapters for the body.

Each adapter wraps the API call to a specific model family and translates
between OpenAI-format messages/tools (the body's lingua franca) and that
model's native format (Hermes XML, Anthropic tool_use, OpenAI function
calling, etc.).

The body is model-agnostic. The adapter is model-specific. The Hand
composes them.

1 Corinthians 9:22: I am made all things to all men, that I might by all
means save some.
"""

from c.adapters.base import Adapter

__all__ = ["Adapter"]
