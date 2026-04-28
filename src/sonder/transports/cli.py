from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.history import InMemoryHistory

from sonder.app import create_default_runtime
from sonder.types import ToolCall

EXIT_COMMANDS = {"q", "quit", "exit"}
SESSION_ID = "cli:local"


def create_prompt_session() -> PromptSession:
    return PromptSession(
        HTML("<ansicyan><b>you</b></ansicyan> <ansibrightblack>›</ansibrightblack> "),
        history=InMemoryHistory(),
        enable_history_search=True,
    )


class CliApp:
    def __init__(
        self,
        runtime,
        prompt_session,
        console: Console | None = None,
    ) -> None:
        self.runtime = runtime
        self.prompt_session = prompt_session
        self.console = console or Console()

    def run(self) -> None:
        self._render_header()
        while True:
            try:
                query = self.prompt_session.prompt()
            except (EOFError, KeyboardInterrupt):
                self._render_goodbye()
                break

            if self._should_exit(query):
                self._render_goodbye()
                break

            self._send(query)

    def _send(self, query: str) -> None:
        tokens: list[str] = []
        self.console.print(Text("assistant ›", style="bold green"))
        waiting = self.console.status(
            "[bold green]thinking...",
            spinner="dots",
            spinner_style="green",
        )
        waiting.start()
        waiting_stopped = False

        def stop_waiting() -> None:
            nonlocal waiting_stopped
            if not waiting_stopped:
                waiting.stop()
                waiting_stopped = True

        def on_token(token: str) -> None:
            stop_waiting()
            tokens.append(token)
            self.console.print(token, end="", style="green", markup=False)

        try:
            reply = self.runtime.handle_user_message(
                session_id=SESSION_ID,
                content=query,
                on_token=on_token,
                on_tool_call=lambda call: self._render_tool_call(call, stop_waiting),
                on_tool_result=lambda call, result: self._render_tool_result(
                    call,
                    result,
                    stop_waiting,
                ),
            )
            stop_waiting()
            if not tokens and reply.content:
                self.console.print(reply.content, style="green", markup=False)
            self.console.print("\n")
        finally:
            stop_waiting()

    def _render_header(self) -> None:
        body = Text()
        body.append("Sonder", style="bold cyan")
        body.append("\n")
        body.append("Type q, quit, or exit to leave.", style="dim")
        self.console.print(
            Panel(
                body,
                title="agent",
                border_style="cyan",
                padding=(1, 2),
            )
        )

    def _render_goodbye(self) -> None:
        self.console.print(Text("bye", style="dim"))

    def _render_tool_call(self, call: ToolCall, stop_waiting) -> None:
        stop_waiting()
        line = Text()
        line.append("• ", style="green")
        line.append("Used ", style="dim")
        line.append(call.name, style="bold blue")
        detail = self._tool_detail(call)
        if detail:
            line.append(f" ({detail})", style="dim")
        self.console.print(line)

    def _render_tool_result(self, call: ToolCall, result: str, stop_waiting) -> None:
        stop_waiting()
        if self._tool_failed(result):
            line = Text()
            line.append("• ", style="red")
            line.append("Failed ", style="dim")
            line.append(call.name, style="bold blue")
            detail = self._tool_detail(call)
            if detail:
                line.append(f" ({detail})", style="dim")
            self.console.print(line)

    def _tool_detail(self, call: ToolCall) -> str:
        command = call.arguments.get("command")
        if isinstance(command, str):
            return command
        if len(call.arguments) == 1:
            value = next(iter(call.arguments.values()))
            return str(value)
        return ""

    def _tool_failed(self, result: str) -> bool:
        first_line = result.splitlines()[0] if result else ""
        return first_line.startswith("exit_code:") and not first_line.endswith(" 0")

    def _should_exit(self, query: str) -> bool:
        normalized = query.strip().lower()
        return normalized == "" or normalized in EXIT_COMMANDS


def main() -> None:
    app = CliApp(
        runtime=create_default_runtime(),
        prompt_session=create_prompt_session(),
    )
    app.run()
