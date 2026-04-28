import argparse
import logging
import sys
from collections.abc import Sequence

from dotenv import load_dotenv

from sonder.app import create_default_runtime
from sonder.gateway.config import DEFAULT_CONFIG_PATH, GatewayAppConfig, load_config
from sonder.logging import configure_logging
from sonder.transports.telegram import TelegramTransport

logger = logging.getLogger(__name__)


class GatewayApp:
    def __init__(self, config: GatewayAppConfig) -> None:
        self.config = config

    def enabled_transport_names(self) -> list[str]:
        names = []
        if self.config.telegram.enabled:
            names.append("telegram")
        return names

    def run(self) -> int:
        names = self.enabled_transport_names()
        if not names:
            raise RuntimeError("No chat transports configured")
        logger.info("Enabled transports: %s", ", ".join(names))
        if self.config.telegram.enabled:
            transport = TelegramTransport(
                runtime=create_default_runtime(),
                token=self._required_token(self.config.telegram.bot_token),
                config=self.config.telegram,
            )
            transport.run()
        return 0

    def _required_token(self, token: str | None) -> str:
        if not token:
            raise RuntimeError("Missing required config value: telegram.bot_token")
        return token


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="sonder-gateway")
    parser.add_argument(
        "--config",
        default=str(DEFAULT_CONFIG_PATH),
        help="Path to gateway TOML config. Defaults to ~/.sonder/config.toml.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    load_dotenv()
    configure_logging(force=True)
    args = build_parser().parse_args(argv)
    try:
        config = load_config(args.config)
        return GatewayApp(config).run()
    except Exception as e:
        logger.error("Error: %s", e)
        return 1
