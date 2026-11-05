"""Tests for local path configuration."""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from skywalker.core.config import Settings


class SettingsTests(unittest.TestCase):
    def test_environment_override_is_used(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            expected = Path(temporary_directory).resolve()
            with patch.dict(os.environ, {"SKYWALKER_DATA_DIR": temporary_directory}):
                settings = Settings.from_environment()

        self.assertEqual(settings.data_directory, expected)

    def test_runtime_paths_are_inside_data_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            settings = Settings(data_directory=Path(temporary_directory))

        self.assertEqual(settings.log_directory, Path(temporary_directory) / "logs")
        self.assertEqual(
            settings.database_path,
            Path(temporary_directory) / "skywalker.sqlite3",
        )
        self.assertEqual(settings.model_directory, Path(temporary_directory) / "models")


if __name__ == "__main__":
    unittest.main()
