from collections.abc import Callable

from sonder.llm.base import LLMProvider, LLMResult, TokenHandler
from sonder.storage.memory import MemorySessionStore
from sonder.tools.registry import ToolRegistry
from sonder.types import AgentReply, Message, ToolCall

MAX_CALLS = 1_0000


class AgentRuntime:
    def __init__(
        self,
        provider: LLMProvider,
        tools: ToolRegistry,
        sessions: MemorySessionStore,
        max_calls: int = MAX_CALLS,
    ) -> None:
        self.provider = provider
        self.tools = tools
        self.sessions = sessions
        self.max_calls = max_calls

    def handle_user_message(
        self,
        session_id: str,
        content: str,
        on_token: TokenHandler | None = None,
        on_tool_call: Callable[[ToolCall], None] | None = None,
        on_tool_result: Callable[[ToolCall, str], None] | None = None,
    ) -> AgentReply:
        messages = self.sessions.get(session_id)
        messages.append(Message(role="user", content=content))

        reply = self._run_agent_loop(
            messages,
            on_token=on_token,
            on_tool_call=on_tool_call,
            on_tool_result=on_tool_result,
        )
        self.sessions.save(session_id, messages)
        return reply

    def _run_agent_loop(
        self,
        messages: list[Message],
        on_token: TokenHandler | None = None,
        on_tool_call: Callable[[ToolCall], None] | None = None,
        on_tool_result: Callable[[ToolCall, str], None] | None = None,
    ) -> AgentReply:
        for _ in range(self.max_calls):
            result = self.provider.chat(messages, self.tools.tools, on_token=on_token)
            self._append_assistant_message(messages, result)

            if not result.tool_calls:
                return AgentReply(content=result.content)

            for call in result.tool_calls:
                if on_tool_call is not None:
                    on_tool_call(call)
                tool_result = self.tools.run(call.name, call.arguments)
                if on_tool_result is not None:
                    on_tool_result(call, tool_result)
                messages.append(
                    Message(role="tool", tool_call_id=call.id, content=tool_result)
                )

        return AgentReply(content="Error: reached maximum agent calls")

    def _append_assistant_message(
        self,
        messages: list[Message],
        result: LLMResult,
    ) -> None:
        messages.append(
            Message(
                role="assistant",
                content=result.content or None,
                tool_calls=result.tool_calls,
                reasoning_content=result.reasoning_content,
            )
        )
