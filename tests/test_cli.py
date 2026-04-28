import io
import unittest
from contextlib import redirect_stderr

from prompt_toolkit import PromptSession
from rich.console import Console

from sonder.transports.cli import CliApp, create_prompt_session


class FakePromptSession:
    def __init__(self, inputs):
        self.inputs = list(inputs)

    def prompt(self):
        if not self.inputs:
            raise EOFError
        return self.inputs.pop(0)


class FakeRuntime:
    def __init__(self):
        self.calls = []

    def handle_user_message(
        self,
        session_id,
        content,
        on_token=None,
        on_tool_call=None,
        on_tool_result=None,
    ):
        self.calls.append((session_id, content))
        call = type(
            "ToolCall",
            (),
            {"name": "Bash", "arguments": {"command": "printf hello"}},
        )()
        if on_tool_call is not None:
            on_tool_call(call)
        if on_tool_result is not None:
            on_tool_result(call, "exit_code: 0\nstdout:\nhello\nstderr:\n")
        if on_token is not None:
            on_token("你好")
        return type("Reply", (), {"content": "你好"})()


class FakeStatus:
    def __init__(self, events):
        self.events = events

    def start(self):
        self.events.append("status:start")

    def stop(self):
        self.events.append("status:stop")


class FakeConsole:
    def __init__(self):
        self.events = []

    def print(self, *args, **kwargs):
        self.events.append(("print", args, kwargs))

    def status(self, *args, **kwargs):
        self.events.append(("status", args, kwargs))
        return FakeStatus(self.events)


class CliTest(unittest.TestCase):
    def test_create_prompt_session_uses_prompt_toolkit(self):
        with redirect_stderr(io.StringIO()):
            session = create_prompt_session()

        self.assertIsInstance(session, PromptSession)

    def test_cli_dispatches_non_exit_input_to_runtime(self):
        runtime = FakeRuntime()
        console = Console(file=io.StringIO(), force_terminal=False, width=80)
        app = CliApp(
            runtime=runtime,
            prompt_session=FakePromptSession(["你好", "q"]),
            console=console,
        )

        app.run()

        self.assertEqual(runtime.calls, [("cli:local", "你好")])

    def test_cli_stops_spinner_before_first_streamed_token(self):
        runtime = FakeRuntime()
        console = FakeConsole()
        app = CliApp(
            runtime=runtime,
            prompt_session=FakePromptSession(["你好", "q"]),
            console=console,
        )

        app.run()

        first_token_index = next(
            i
            for i, event in enumerate(console.events)
            if isinstance(event, tuple) and event[0] == "print" and event[1] == ("你好",)
        )
        self.assertLess(console.events.index("status:start"), first_token_index)
        self.assertLess(console.events.index("status:stop"), first_token_index)

    def test_cli_renders_compact_tool_call_trace(self):
        runtime = FakeRuntime()
        console_file = io.StringIO()
        console = Console(file=console_file, force_terminal=False, width=100)
        app = CliApp(
            runtime=runtime,
            prompt_session=FakePromptSession(["run command", "q"]),
            console=console,
        )

        app.run()

        output = console_file.getvalue()
        self.assertIn("Used Bash", output)
        self.assertIn("printf hello", output)
        self.assertNotIn("tool call", output)
        self.assertNotIn("tool result", output)
        self.assertNotIn("stdout:", output)


if __name__ == "__main__":
    unittest.main()
