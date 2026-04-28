from copy import deepcopy

from sonder.types import Message

DEFAULT_SYSTEM_MESSAGE = Message(role="system", content="你是一个有用的助手")


class MemorySessionStore:
    def __init__(self, system_message: Message | None = None) -> None:
        self._system_message = system_message or DEFAULT_SYSTEM_MESSAGE
        self._sessions: dict[str, list[Message]] = {}

    def get(self, session_id: str) -> list[Message]:
        if session_id not in self._sessions:
            self._sessions[session_id] = [deepcopy(self._system_message)]
        return self._sessions[session_id]

    def save(self, session_id: str, messages: list[Message]) -> None:
        self._sessions[session_id] = messages
