import json
import os
from typing import Any

from openai import OpenAI, Stream
from openai.types.chat.chat_completion_chunk import ChatCompletionChunk

from sonder.llm.base import LLMProvider, LLMResult, TokenHandler
from sonder.types import Message, ToolCall, ToolDefinition


class OpenAIChatProvider(LLMProvider):
    def __init__(
        self,
        model: str,
        base_url: str | None = None,
        api_key: str | None = None,
    ) -> None:
        self.model = model
        self.client = OpenAI(
            base_url=base_url,
            api_key=api_key or os.environ.get("OPENAI_API_KEY"),
        )

    def chat(
        self,
        messages: list[Message],
        tools: list[ToolDefinition],
        on_token: TokenHandler | None = None,
    ) -> LLMResult:
        stream: Stream[ChatCompletionChunk] = self.client.chat.completions.create(
            model=self.model,
            messages=[self._to_openai_message(message) for message in messages],
            stream=True,
            tools=[self._to_openai_tool(tool) for tool in tools],
        )
        full_content = ""
        reasoning_content = ""
        raw_tool_calls: dict[int, dict[str, Any]] = {}

        for chunk in stream:
            for choice in chunk.choices:
                delta = choice.delta
                if rc := getattr(delta, "reasoning_content", None):
                    reasoning_content += rc
                if content := delta.content:
                    full_content += content
                    if on_token is not None:
                        on_token(content)
                if tcs := delta.tool_calls:
                    self._collect_tool_call_deltas(raw_tool_calls, tcs)

        return LLMResult(
            content=full_content,
            tool_calls=self._parse_tool_calls(raw_tool_calls),
            reasoning_content=reasoning_content or None,
        )

    def _collect_tool_call_deltas(self, tool_calls: dict[int, dict[str, Any]], deltas) -> None:
        for tc in deltas:
            current = tool_calls.setdefault(
                tc.index,
                {
                    "id": "",
                    "type": "function",
                    "function": {"name": "", "arguments": ""},
                },
            )
            if tid := tc.id:
                current["id"] = tid
            if fun := tc.function:
                if fun_name := fun.name:
                    current["function"]["name"] += fun_name
                if fun_args := fun.arguments:
                    current["function"]["arguments"] += fun_args

    def _parse_tool_calls(self, raw_tool_calls: dict[int, dict[str, Any]]) -> list[ToolCall]:
        calls = []
        for raw_call in raw_tool_calls.values():
            function = raw_call["function"]
            args_json = function["arguments"] or "{}"
            calls.append(
                ToolCall(
                    id=raw_call["id"],
                    name=function["name"],
                    arguments=json.loads(args_json),
                )
            )
        return calls

    def _to_openai_message(self, message: Message) -> dict[str, Any]:
        data: dict[str, Any] = {
            "role": message.role,
            "content": message.content,
        }
        if message.tool_calls:
            data["tool_calls"] = [
                call.to_chat_completion_tool_call() for call in message.tool_calls
            ]
        if message.tool_call_id:
            data["tool_call_id"] = message.tool_call_id
        if message.reasoning_content:
            data["reasoning_content"] = message.reasoning_content
        return data

    def _to_openai_tool(self, tool: ToolDefinition) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters,
                "strict": tool.strict,
            },
        }
