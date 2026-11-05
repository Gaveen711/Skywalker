"""Local application path configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class Settings:
    """Filesystem locations used by the local application foundation."""

    data_directory: Path
    ollama_url: str = "http://127.0.0.1:11434"
    model_name: str = "qwen3.5:4b"
    system_prompt: str = "You are Sky Walker, a helpful private desktop assistant. Be clear and concise."

    @classmethod
    def from_environment(cls) -> Settings:
        """Create settings using an optional local data-directory override."""
        override = os.environ.get("SKYWALKER_DATA_DIR", "").strip()
        if override:
            data_directory = Path(override).expanduser()
        elif os.name == "nt":
            local_app_data = os.environ.get("LOCALAPPDATA")
            base_directory = Path(local_app_data) if local_app_data else Path.home() / "AppData" / "Local"
            data_directory = base_directory / "SkyWalker"
        else:
            data_directory = Path.home() / ".local" / "share" / "skywalker"

        return cls(
            data_directory=data_directory.resolve(),
            ollama_url=os.environ.get("SKYWALKER_OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/"),
            model_name=os.environ.get("SKYWALKER_MODEL", "qwen3.5:4b").strip(),
            system_prompt=os.environ.get(
                "SKYWALKER_SYSTEM_PROMPT",
                "You are Sky Walker, a helpful private desktop assistant. Be clear and concise.",
            ),
        )

    @property
    def log_directory(self) -> Path:
        """Directory for local application logs."""
        return self.data_directory / "logs"

    @property
    def database_path(self) -> Path:
        """Future local SQLite database path."""
        return self.data_directory / "skywalker.sqlite3"

    @property
    def model_directory(self) -> Path:
        """Directory reserved for locally downloaded models."""
        return self.data_directory / "models"
