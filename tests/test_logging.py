"""Tests for local logging setup."""

import logging
import tempfile
import unittest
from pathlib import Path

from skywalker.core.logging import configure_logging


class LoggingTests(unittest.TestCase):
    def test_configure_logging_creates_one_rotating_file_handler(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            logger = configure_logging(Path(temporary_directory))
            try:
                logger.info("foundation test message")

                log_file = Path(temporary_directory) / "skywalker.log"
                self.assertTrue(log_file.is_file())
                self.assertIn("foundation test message", log_file.read_text(encoding="utf-8"))

                handler_count = len(logger.handlers)
                configure_logging(Path(temporary_directory))
                self.assertEqual(len(logger.handlers), handler_count)
            finally:
                for handler in tuple(logger.handlers):
                    logger.removeHandler(handler)
                    handler.close()


if __name__ == "__main__":
    unittest.main()
