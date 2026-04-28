import unittest

from sonder.llm.base import LLMProvider, LLMResult
from sonder.runtime.agent import AgentRuntime
from sonder.storage.memory import MemorySessionStore
from sonder.tools.registry import ToolRegistry
from pydantic import ValidationError

from sonder.types import Message, ToolCall, ToolDefinition


class FakeProvider(LLMProvider):
    def __init__(self, results):
        self.results = list(results)
        self.calls = []

    def chat(self, messages, tools, on_token=None):
        self.calls.append((list(messages), list(tools)))
        return self.results.pop(0)


class AgentRuntimeTest(unittest.TestCase):
    def test_returns_assistant_content(self):
        provider = FakeProvider([LLMResult(content="hello")])
        runtime = AgentRuntime(
            provider=provider,
            tools=ToolRegistry(),
            sessions=MemorySessionStore(),
        )

        reply = runtime.handle_user_message("cli:local", "hi")

        self.assertEqual(reply.content, "hello")

    def test_executes_tool_call_and_continues_until_text_reply(self):
        registry = ToolRegistry()
        registry.register(
            ToolDefinition(
                name="Echo",
                description="Echo text",
                parameters={
                    "type": "object",
                    "properties": {"text": {"type": "string"}},
                    "required": ["text"],
                    "additionalProperties": False,
                },
            ),
            lambda text: text,
        )
        provider = FakeProvider(
            [
                LLMResult(
                    content="",
                    tool_calls=[ToolCall(id="call-1", name="Echo", arguments={"text": "ok"})],
                ),
                LLMResult(content="tool said ok"),
            ]
        )
        runtime = AgentRuntime(
            provider=provider,
            tools=registry,
            sessions=MemorySessionStore(),
        )

        reply = runtime.handle_user_message("cli:local", "use tool")

        self.assertEqual(reply.content, "tool said ok")
        self.assertEqual(len(provider.calls), 2)

    def test_reports_tool_call_and_result_events(self):
        registry = ToolRegistry()
        registry.register(
            ToolDefinition(
                name="Echo",
                description="Echo text",
                parameters={
                    "type": "object",
                    "properties": {"text": {"type": "string"}},
                    "required": ["text"],
                    "additionalProperties": False,
                },
            ),
            lambda text: text,
        )
        provider = FakeProvider(
            [
                LLMResult(
                    content="",
                    tool_calls=[
                        ToolCall(id="call-1", name="Echo", arguments={"text": "ok"})
                    ],
                ),
                LLMResult(content="done"),
            ]
        )
        runtime = AgentRuntime(
            provider=provider,
            tools=registry,
            sessions=MemorySessionStore(),
        )
        events = []

        runtime.handle_user_message(
            "cli:local",
            "use tool",
            on_tool_call=lambda call: events.append(("call", call.name, call.arguments)),
            on_tool_result=lambda call, result: events.append(("result", call.name, result)),
        )

        self.assertEqual(
            events,
            [
                ("call", "Echo", {"text": "ok"}),
                ("result", "Echo", "ok"),
            ],
        )

    def test_tool_call_validates_arguments_default(self):
        call = ToolCall.model_validate({"id": "call-1", "name": "Echo"})

        self.assertEqual(call.arguments, {})

    def test_tool_call_dumps_openai_tool_call_shape(self):
        call = ToolCall(id="call-1", name="Echo", arguments={"text": "ok"})

        dumped = call.to_chat_completion_tool_call()

        self.assertEqual(dumped["id"], "call-1")
        self.assertEqual(dumped["type"], "function")
        self.assertEqual(dumped["function"]["name"], "Echo")
        self.assertEqual(dumped["function"]["arguments"], '{"text": "ok"}')

    def test_message_rejects_unknown_role(self):
        with self.assertRaises(ValidationError):
            Message.model_validate({"role": "developer", "content": "nope"})

    def test_tool_definition_rejects_missing_handler_name(self):
        with self.assertRaises(ValidationError):
            ToolDefinition.model_validate(
                {
                    "description": "Echo text",
                    "parameters": {"type": "object"},
                }
            )


if __name__ == "__main__":
    unittest.main()
