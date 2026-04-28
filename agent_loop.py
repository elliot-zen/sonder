import os
from openai import OpenAI, Stream
from openai.types.chat.chat_completion_chunk import ChatCompletionChunk
from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam
from openai.types.chat.chat_completion_tool_param import ChatCompletionToolParam
from dotenv import load_dotenv
from rich.prompt import Prompt
from rich.console import Console

_ = load_dotenv()

client = OpenAI(
    base_url="https://api.deepseek.com", api_key=os.environ.get("OPENAI_API_KEY")
)

history: list[ChatCompletionMessageParam] = [
    {"role": "system", "content": "你是一个有用的助手"}
]
console = Console()


def read_file(path: str):
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    return lines


TOOL_HANDLERS = {"read_file": lambda **kw: read_file(kw["path"])}
TOOLS: list[ChatCompletionToolParam] = [
    {
        "type": "function",
        "function": {
            "name": "ReadFile",
            "description": "read file contents.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "the file path."}
                },
                "required": ["path"],
                "additionalProperties": False,
            },
            "strict": True,
        },
    }
]


def agent_loop():
    with console.status("[bold green]Thinking...[/bold green]", spinner="dots"):
        stream: Stream[ChatCompletionChunk] = client.chat.completions.create(
            model="deepseek-v4-flash",
            messages=history,
            stream=True,
            tools=TOOLS,
        )
    full_content: str = ""
    console.print("[bold cyan]AI:[/bold cyan]", end="")
    for chunk in stream:
        for choice in chunk.choices:
            delta = choice.delta
            if content := delta.content:
                full_content += content
                console.print(content, end="", style="green")
        if usage := chunk.usage:
            console.print(f"\nCost: {usage.total_tokens} Token", style="blue")
    history.append(
        {
            "role": "assistant",
            "content": full_content,
        }
    )


def main():
    while True:
        query = Prompt.ask("[bold cyan]>>[/bold cyan]")
        if query.strip().lower() in ("q", "exit", ""):
            break
        history.append(
            {
                "role": "user",
                "content": query,
            }
        )
        agent_loop()


if __name__ == "__main__":
    main()
