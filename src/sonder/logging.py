import logging
import re
import sys
from typing import TextIO

LOG_FORMAT = "%(asctime)s %(levelname)s [%(name)s] %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
TELEGRAM_BOT_TOKEN_PATTERN = re.compile(r"bot[^/\s]+")


class RedactSecretsFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        redacted = redact_secrets(message)
        record.msg = redacted
        record.args = ()
        return True


def redact_secrets(message: str) -> str:
    return TELEGRAM_BOT_TOKEN_PATTERN.sub("bot<redacted>", message)


def configure_logging(
    level: int | str = logging.INFO,
    stream: TextIO | None = None,
    force: bool = False,
) -> None:
    logging.basicConfig(
        level=level,
        format=LOG_FORMAT,
        datefmt=DATE_FORMAT,
        stream=stream or sys.stderr,
        force=force,
    )
    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        handler.addFilter(RedactSecretsFilter())

    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("telegram").setLevel(logging.WARNING)
