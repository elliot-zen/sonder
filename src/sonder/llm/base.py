from abc import ABC, abstractmethod
from typing import Callable

from pydantic import BaseModel, Field

from sonder.types import Message, ToolCall, ToolDefinition


TokenHandler = Callable[[str], None]


class LLMResult(BaseModel):
    content: str
    tool_calls: list[ToolCall] = Field(default_factory=list)
    reasoning_content: str | None = None


class LLMProvider(ABC):
    @abstractmethod
    def chat(
        self,
        messages: list[Message],
        tools: list[ToolDefinition],
        on_token: TokenHandler | None = None,
    ) -> LLMResult:
        pass
