"""Privacy-conscious local rotating log configuration."""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOGGER_NAME = "skywalker"
MAX_LOG_BYTES = 2_000_000
BACKUP_COUNT = 3


def configure_logging(log_directory: Path, level: int = logging.INFO) -> logging.Logger:
    """Configure one rotating file log without duplicating handlers."""
    log_directory.mkdir(parents=True, exist_ok=True)
    log_path = (log_directory / "skywalker.log").resolve()
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(level)
    logger.propagate = False

    if not any(
        isinstance(handler, RotatingFileHandler)
        and Path(handler.baseFilename).resolve() == log_path
        for handler in logger.handlers
    ):
        handler = RotatingFileHandler(
            log_path,
            maxBytes=MAX_LOG_BYTES,
            backupCount=BACKUP_COUNT,
            encoding="utf-8",
        )
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
        )
        logger.addHandler(handler)

    return logger
