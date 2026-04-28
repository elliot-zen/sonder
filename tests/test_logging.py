import io
import logging
import unittest

from sonder.logging import configure_logging


class LoggingTest(unittest.TestCase):
    def test_configure_logging_uses_standard_format(self):
        stream = io.StringIO()

        configure_logging(stream=stream, force=True)
        logging.getLogger("sonder.test").info("hello")

        output = stream.getvalue()
        self.assertIn("INFO", output)
        self.assertIn("sonder.test", output)
        self.assertIn("hello", output)

    def test_configure_logging_redacts_telegram_bot_token_in_urls(self):
        stream = io.StringIO()
        configure_logging(stream=stream, force=True)

        logging.getLogger("httpx").warning(
            'HTTP Request: POST https://api.telegram.org/bot123456:secret-token/sendMessage "HTTP/1.1 200 OK"'
        )

        output = stream.getvalue()
        self.assertIn("bot<redacted>/sendMessage", output)
        self.assertNotIn("123456:secret-token", output)

    def test_configure_logging_raises_httpx_default_level_to_warning(self):
        configure_logging(force=True)

        self.assertEqual(logging.getLogger("httpx").level, logging.WARNING)
