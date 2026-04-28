from typing import Any

from pydantic import BaseModel, Field
from typing_extensions import Literal


MessageRole = Literal["system", "user", "assistant", "tool"]


class Message(BaseModel):
    role: MessageRole
    content: str | None = None
    tool_calls: list["ToolCall"] = Field(default_factory=list)
    tool_call_id: str | None = None
    reasoning_content: str | None = None


class ToolDefinition(BaseModel):
    name: str
    description: str
    parameters: dict[str, Any]
    strict: bool = True


class ToolCall(BaseModel):
    id: str
    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)

    def to_chat_completion_tool_call(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": "function",
            "function": {
                "name": self.name,
                "arguments": self.arguments_json,
            },
        }

    @property
    def arguments_json(self) -> str:
        import json

        return json.dumps(self.arguments, ensure_ascii=False)


class AgentReply(BaseModel):
    content: str
