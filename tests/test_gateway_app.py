import importlib
import tempfile
import unittest
import io
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from pydantic import ValidationError

from sonder.gateway.app import GatewayApp, main
from sonder.gateway.config import GatewayAppConfig, TelegramConfig


class GatewayAppTest(unittest.TestCase):
    def test_gateway_entrypoint_exists(self):
        app = importlib.import_module("sonder.gateway.app")

        self.assertTrue(callable(app.main))

    def test_enabled_transport_names_includes_telegram(self):
        app = GatewayApp(
            GatewayAppConfig(
                telegram=TelegramConfig(
                    enabled=True,
                    bot_token="123456:token",
                    allowed_users=["123456789"],
                )
            )
        )

        self.assertEqual(app.enabled_transport_names(), ["telegram"])

    def test_raises_when_no_transports_are_enabled(self):
        app = GatewayApp(GatewayAppConfig())

        with self.assertRaisesRegex(RuntimeError, "No chat transports configured"):
            app.run()

    def test_main_loads_config_argument_and_prints_enabled_transport(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "config.toml"
            path.write_text(
                """
[telegram]
enabled = true
bot_token = "123456:token"
allowed_users = ["123456789"]
""".strip(),
                encoding="utf-8",
            )
            stderr = io.StringIO()
            with patch("sonder.gateway.app.create_default_runtime"):
                with patch("sonder.gateway.app.TelegramTransport"):
                    with redirect_stderr(stderr):
                        exit_code = main(["--config", str(path)])

        self.assertEqual(exit_code, 0)
        self.assertIn("Enabled transports: telegram", stderr.getvalue())

    def test_gateway_starts_telegram_transport_with_config_token(self):
        config = GatewayAppConfig(
            telegram=TelegramConfig(
                enabled=True,
                bot_token="123456:token",
                allowed_users=["123456789"],
            )
        )

        with patch("sonder.gateway.app.create_default_runtime") as create_runtime:
            with patch("sonder.gateway.app.TelegramTransport") as transport_cls:
                app = GatewayApp(config)
                exit_code = app.run()

        self.assertEqual(exit_code, 0)
        transport_cls.assert_called_once_with(
            runtime=create_runtime.return_value,
            token="123456:token",
            config=config.telegram,
        )
        transport_cls.return_value.run.assert_called_once_with()

    def test_gateway_requires_telegram_token_value(self):
        with self.assertRaises(ValidationError):
            GatewayAppConfig(
                telegram=TelegramConfig(
                    enabled=True,
                    bot_token="",
                    allowed_users=["123456789"],
                )
            )

    def test_main_prints_startup_error_without_traceback(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "config.toml"
            path.write_text(
                """
[telegram]
enabled = true
bot_token = ""
allowed_users = ["123456789"]
""".strip(),
                encoding="utf-8",
            )
            stderr = io.StringIO()
            with redirect_stderr(stderr):
                exit_code = main(["--config", str(path)])

        self.assertEqual(exit_code, 1)
        self.assertIn("Error:", stderr.getvalue())
        self.assertNotIn("Traceback", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
