import subprocess

from sonder.tools.registry import ToolRegistry
from sonder.types import ToolDefinition


BASH_TOOL = ToolDefinition(
    name="Bash",
    description="Run a bash command in the current workspace and return exit code, stdout, and stderr.",
    parameters={
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "The bash command to run.",
            },
            "timeout": {
                "type": "integer",
                "description": "Maximum runtime in seconds.",
                "default": 30,
            },
        },
        "required": ["command"],
        "additionalProperties": False,
    },
    strict=True,
)


def bash(command: str, timeout: int = 30) -> str:
    try:
        completed = subprocess.run(
            ["bash", "-lc", command],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as e:
        stdout = e.stdout or ""
        stderr = e.stderr or ""
        return _format_result(
            exit_code="timeout",
            stdout=stdout,
            stderr=f"Command timed out after {timeout}s\n{stderr}".strip(),
        )
    except Exception as e:
        return f"Error: {e}"

    return _format_result(
        exit_code=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )


def _format_result(exit_code: int | str, stdout: str, stderr: str) -> str:
    return f"exit_code: {exit_code}\nstdout:\n{stdout}\nstderr:\n{stderr}"


def create_default_tool_registry() -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(BASH_TOOL, bash)
    return registry

