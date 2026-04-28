import tempfile
import unittest
from pathlib import Path

from pydantic import ValidationError

from sonder.gateway.config import (
    DEFAULT_CONFIG_PATH,
    GatewayAppConfig,
    TelegramConfig,
    load_config,
)


class GatewayConfigTest(unittest.TestCase):
    def test_default_config_path_uses_home_sonder_config_toml(self):
        self.assertEqual(DEFAULT_CONFIG_PATH, Path.home() / ".sonder" / "config.toml")

    def test_loads_simple_telegram_config(self):
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

            config = load_config(path)

        self.assertTrue(config.telegram.enabled)
        self.assertEqual(config.telegram.bot_token, "123456:token")
        self.assertEqual(config.telegram.allowed_users, ["123456789"])

    def test_telegram_token_is_required_when_enabled(self):
        with self.assertRaises(ValidationError):
            GatewayAppConfig.model_validate({"telegram": {"enabled": True}})

    def test_disabled_telegram_config_can_omit_token(self):
        config = GatewayAppConfig(
            telegram=TelegramConfig(enabled=False),
        )

        self.assertFalse(config.telegram.enabled)


if __name__ == "__main__":
    unittest.main()
