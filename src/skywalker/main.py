"""Desktop application entry point."""

import sys

from skywalker.core.config import Settings
from skywalker.core.logging import configure_logging


def main() -> int:
    """Start the Qt desktop application."""
    settings = Settings.from_environment()
    logger = configure_logging(settings.log_directory)
    from PySide6.QtWidgets import QApplication

    from skywalker.presentation.window import MainWindow

    app = QApplication(sys.argv)
    app.setApplicationName("Sky Walker")
    window = MainWindow()
    window.show()
    logger.info("Sky Walker desktop started")
    return app.exec()
