from dotenv import load_dotenv

from sonder.llm.openai_chat import OpenAIChatProvider
from sonder.runtime.agent import AgentRuntime
from sonder.storage.memory import MemorySessionStore
from sonder.tools.bash_tools import create_default_tool_registry


def create_default_runtime() -> AgentRuntime:
    load_dotenv()
    return AgentRuntime(
        provider=OpenAIChatProvider(
            model="deepseek-v4-flash",
            base_url="https://api.deepseek.com",
        ),
        tools=create_default_tool_registry(),
        sessions=MemorySessionStore(),
    )
