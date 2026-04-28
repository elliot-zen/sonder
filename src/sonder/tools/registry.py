from collections.abc import Callable
from typing import Any

from sonder.types import ToolDefinition

ToolHandler = Callable[..., str]


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = {}
        self._handlers: dict[str, ToolHandler] = {}

    def register(self, tool: ToolDefinition, handler: ToolHandler) -> None:
        self._tools[tool.name] = tool
        self._handlers[tool.name] = handler

    @property
    def tools(self) -> list[ToolDefinition]:
        return list(self._tools.values())

    def run(self, name: str, arguments: dict[str, Any]) -> str:
        handler = self._handlers.get(name)
        if handler is None:
            return f"Error: unknown tool {name}"
        try:
            return handler(**arguments)
        except Exception as e:
            return f"Error: {e}"
