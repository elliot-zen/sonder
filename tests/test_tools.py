import unittest

from sonder.tools.bash_tools import bash, create_default_tool_registry
from sonder.tools.registry import ToolRegistry
from sonder.types import ToolDefinition


class ToolRegistryTest(unittest.TestCase):
    def test_runs_registered_tool(self):
        registry = ToolRegistry()
        registry.register(
            ToolDefinition(
                name="Echo",
                description="Echo text",
                parameters={
                    "type": "object",
                    "properties": {"text": {"type": "string"}},
                    "required": ["text"],
                    "additionalProperties": False,
                },
            ),
            lambda text: text.upper(),
        )

        result = registry.run("Echo", {"text": "hello"})

        self.assertEqual(result, "HELLO")

    def test_returns_error_for_unknown_tool(self):
        registry = ToolRegistry()

        result = registry.run("Missing", {})

        self.assertEqual(result, "Error: unknown tool Missing")

    def test_bash_returns_stdout_and_exit_code(self):
        result = bash("printf hello")

        self.assertIn("exit_code: 0", result)
        self.assertIn("stdout:\nhello", result)

    def test_bash_returns_stderr_for_failed_command(self):
        result = bash("ls does-not-exist-for-sonder-test")

        self.assertIn("exit_code:", result)
        self.assertIn("stderr:", result)

    def test_default_registry_registers_bash_not_read_file(self):
        registry = create_default_tool_registry()

        tool_names = [tool.name for tool in registry.tools]

        self.assertEqual(tool_names, ["Bash"])


if __name__ == "__main__":
    unittest.main()
