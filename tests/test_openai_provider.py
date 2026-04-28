import unittest

from sonder.llm.openai_chat import OpenAIChatProvider
from sonder.types import Message, ToolCall, ToolDefinition


class OpenAIChatProviderConversionTest(unittest.TestCase):
    def setUp(self):
        self.provider = OpenAIChatProvider(
            model="test-model",
            base_url="https://example.invalid",
            api_key="test-key",
        )

    def test_converts_internal_message_to_openai_message(self):
        message = Message(
            role="assistant",
            content=None,
            tool_calls=[
                ToolCall(id="call-1", name="Echo", arguments={"text": "hello"})
            ],
            reasoning_content="thinking",
        )

        converted = self.provider._to_openai_message(message)

        self.assertEqual(converted["role"], "assistant")
        self.assertIsNone(converted["content"])
        self.assertEqual(converted["reasoning_content"], "thinking")
        self.assertEqual(converted["tool_calls"][0]["function"]["name"], "Echo")
        self.assertEqual(
            converted["tool_calls"][0]["function"]["arguments"],
            '{"text": "hello"}',
        )

    def test_converts_internal_tool_to_openai_tool_schema(self):
        tool = ToolDefinition(
            name="Echo",
            description="Echo text",
            parameters={"type": "object"},
            strict=False,
        )

        converted = self.provider._to_openai_tool(tool)

        self.assertEqual(converted["type"], "function")
        self.assertEqual(converted["function"]["name"], "Echo")
        self.assertEqual(converted["function"]["description"], "Echo text")
        self.assertEqual(converted["function"]["parameters"], {"type": "object"})
        self.assertFalse(converted["function"]["strict"])


if __name__ == "__main__":
    unittest.main()
