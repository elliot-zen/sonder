import asyncio
import logging
from typing import Any

from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

from sonder.gateway.config import TelegramConfig

logger = logging.getLogger(__name__)
MESSAGE_PREVIEW_LIMIT = 120


class TelegramTransport:
    def __init__(self, runtime, token: str, config: TelegramConfig) -> None:
        self.runtime = runtime
        self.token = token
        self.config = config

    def run(self) -> None:
        application = (
            ApplicationBuilder()
            .token(self.token)
            .build()
        )
        application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text)
        )
        logger.info("Starting telegram transport")
        application.run_polling()

    async def handle_text(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE | None,
    ) -> None:
        message = update.message
        user = update.effective_user
        chat = update.effective_chat
        if message is None or user is None or chat is None or message.text is None:
            logger.debug("Ignoring telegram update without text message")
            return

        user_id = str(user.id)
        if not self._is_authorized(user_id):
            logger.warning("Rejected unauthorized telegram user_id=%s", user_id)
            await message.reply_text("Unauthorized")
            return
        logger.info(
            "Received telegram message chat_id=%s user_id=%s text=%s",
            chat.id,
            user_id,
            self._message_preview(message.text),
        )

        tool_lines: list[str] = []

        def on_tool_call(call: Any) -> None:
            logger.info("Telegram tool call name=%s detail=%s", call.name, self._tool_detail(call))
            tool_lines.append(self._format_tool_call(call))

        reply = await asyncio.to_thread(
            self.runtime.handle_user_message,
            self._session_id(str(chat.id), user_id),
            message.text,
            on_tool_call=on_tool_call,
        )

        for line in tool_lines:
            await message.reply_text(line)
        if reply.content:
            await message.reply_text(reply.content)

    def _is_authorized(self, user_id: str) -> bool:
        return not self.config.allowed_users or user_id in self.config.allowed_users

    def _session_id(self, chat_id: str, user_id: str) -> str:
        return f"telegram:{chat_id}:{user_id}"

    def _format_tool_call(self, call: Any) -> str:
        detail = self._tool_detail(call)
        if detail:
            return f"Used {call.name} (`{detail}`)"
        return f"Used {call.name}"

    def _tool_detail(self, call: Any) -> str:
        command = call.arguments.get("command")
        if isinstance(command, str):
            return command
        if len(call.arguments) == 1:
            return str(next(iter(call.arguments.values())))
        return ""

    def _message_preview(self, text: str) -> str:
        normalized = " ".join(text.split())
        if len(normalized) <= MESSAGE_PREVIEW_LIMIT:
            return normalized
        return f"{normalized[:MESSAGE_PREVIEW_LIMIT]}..."
