import unittest

from sonder.gateway.config import TelegramConfig
from sonder.transports.telegram import TelegramTransport


class FakeReplyMessage:
    def __init__(self, text, chat_id, user_id):
        self.text = text
        self.chat_id = chat_id
        self.from_user = type("User", (), {"id": user_id})()
        self.replies = []

    async def reply_text(self, text, **kwargs):
        self.replies.append((text, kwargs))


class FakeUpdate:
    def __init__(self, text="hello", chat_id=100, user_id=123):
        self.message = FakeReplyMessage(text=text, chat_id=chat_id, user_id=user_id)
        self.effective_user = self.message.from_user
        self.effective_chat = type("Chat", (), {"id": chat_id})()


class FakeRuntime:
    def __init__(self):
        self.calls = []

    def handle_user_message(self, session_id, content, **kwargs):
        self.calls.append((session_id, content, kwargs))
        on_tool_call = kwargs.get("on_tool_call")
        if on_tool_call is not None:
            on_tool_call(type("Call", (), {"name": "Bash", "arguments": {"command": "pwd"}})())
        return type("Reply", (), {"content": "world"})()


class TelegramTransportTest(unittest.IsolatedAsyncioTestCase):
    async def test_authorized_message_calls_runtime_and_replies(self):
        runtime = FakeRuntime()
        transport = TelegramTransport(
            runtime=runtime,
            token="token",
            config=TelegramConfig(
                enabled=True,
                bot_token="123456:token",
                allowed_users=["123"],
            ),
        )
        update = FakeUpdate(text="hello", chat_id=100, user_id=123)

        await transport.handle_text(update, None)

        self.assertEqual(runtime.calls[0][0], "telegram:100:123")
        self.assertEqual(runtime.calls[0][1], "hello")
        self.assertEqual(update.message.replies[-1][0], "world")

    async def test_unauthorized_user_is_rejected(self):
        runtime = FakeRuntime()
        transport = TelegramTransport(
            runtime=runtime,
            token="token",
            config=TelegramConfig(
                enabled=True,
                bot_token="123456:token",
                allowed_users=["999"],
            ),
        )
        update = FakeUpdate(text="hello", chat_id=100, user_id=123)

        with self.assertLogs("sonder.transports.telegram", level="WARNING") as logs:
            await transport.handle_text(update, None)

        self.assertEqual(runtime.calls, [])
        self.assertEqual(update.message.replies[-1][0], "Unauthorized")
        self.assertIn("Rejected unauthorized telegram user_id=123", "\n".join(logs.output))

    async def test_formats_tool_call_as_compact_line(self):
        runtime = FakeRuntime()
        transport = TelegramTransport(
            runtime=runtime,
            token="token",
            config=TelegramConfig(
                enabled=True,
                bot_token="123456:token",
                allowed_users=["123"],
            ),
        )
        update = FakeUpdate(text="hello", chat_id=100, user_id=123)

        await transport.handle_text(update, None)

        self.assertEqual(update.message.replies[0][0], "Used Bash (`pwd`)")

    async def test_logs_received_message_with_truncation(self):
        runtime = FakeRuntime()
        transport = TelegramTransport(
            runtime=runtime,
            token="token",
            config=TelegramConfig(
                enabled=True,
                bot_token="123456:token",
                allowed_users=["123"],
            ),
        )
        long_text = "x" * 240
        update = FakeUpdate(text=long_text, chat_id=100, user_id=123)

        with self.assertLogs("sonder.transports.telegram", level="INFO") as logs:
            await transport.handle_text(update, None)

        output = "\n".join(logs.output)
        self.assertIn("Received telegram message chat_id=100 user_id=123 text=", output)
        self.assertIn("...", output)
        self.assertNotIn(long_text, output)

    def test_message_preview_normalizes_newlines(self):
        transport = TelegramTransport(
            runtime=FakeRuntime(),
            token="token",
            config=TelegramConfig(enabled=True, bot_token="123456:token"),
        )

        self.assertEqual(transport._message_preview("hello\nworld"), "hello world")


if __name__ == "__main__":
    unittest.main()
