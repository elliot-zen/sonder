import os
import json
from openai import OpenAI, Stream
from openai.types.chat.chat_completion_chunk import ChatCompletionChunk
from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam
from openai.types.chat.chat_completion_tool_param import ChatCompletionToolParam
from dotenv import load_dotenv
from rich.prompt import Prompt
from rich.console import Console

MAX_CALLS = 1_0000
_ = load_dotenv()

client = OpenAI(
    base_url="https://api.deepseek.com", api_key=os.environ.get("OPENAI_API_KEY")
)

history: list[ChatCompletionMessageParam] = [
    {"role": "system", "content": "你是一个有用的助手"}
]
console = Console()


def read_file(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


TOOL_HANDLERS = {"ReadFile": lambda **kw: read_file(kw["path"])}
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
    for _ in range(MAX_CALLS):
        stream: Stream[ChatCompletionChunk] = client.chat.completions.create(
            model="deepseek-v4-flash",
            messages=history,
            stream=True,
            tools=TOOLS,
        )
        full_content: str = ""
        reasoning_content: str = ""
        tool_calls = {}
        finish_reason = None
        for chunk in stream:
            for choice in chunk.choices:
                finish_reason = choice.finish_reason or finish_reason
                delta = choice.delta
                # DeepSeek-specific field required for thinking mode multi-turn/tool-call history.
                if rc := getattr(delta, "reasoning_content", None):
                    reasoning_content += rc
                if content := delta.content:
                    full_content += content
                    console.print(content, end="", style="green", markup=False)
                if tcs := delta.tool_calls:
                    for tc in tcs:
                        i = tc.index
                        current = tool_calls.setdefault(
                            i,
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

        console.print()
        if tool_calls:
            calls = list(tool_calls.values())
            history.append(
                {
                    "role": "assistant",
                    "content": full_content or None,
                    "tool_calls": calls,
                    "reasoning_content": reasoning_content,
                }
            )
            for call in calls:
                name = call["function"]["name"]
                args_json = call["function"]["arguments"] or "{}"
                args = json.loads(args_json)
                result = TOOL_HANDLERS[name](**args)
                console.print(f"[bold blue]Tool {name} : {args}[/bold blue]")
                history.append(
                    {"role": "tool", "tool_call_id": call["id"], "content": result}
                )
            continue
        # No tool call
        history.append(
            {
                "role": "assistant",
                "content": full_content,
                "reasoning_content": reasoning_content,
            }
        )
        break


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
