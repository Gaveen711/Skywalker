"""Ollama local inference adapter using its streamed HTTP API."""

from __future__ import annotations

import json
from collections.abc import Iterator, Sequence
from threading import Event
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from skywalker.core.config import Settings
from skywalker.domain.ai import ChatMessage


class OllamaError(RuntimeError):
    """Raised when the local Ollama service cannot fulfill a request."""


class OllamaProvider:
    def __init__(self, settings: Settings, timeout: float = 5.0) -> None:
        self.base_url = settings.ollama_url
        self.system_prompt = settings.system_prompt
        self.timeout = timeout

    def list_models(self) -> list[str]:
        request = Request(f"{self.base_url}/api/tags")
        try:
            with urlopen(request, timeout=self.timeout) as response:
                data = json.load(response)
        except (OSError, URLError, HTTPError, json.JSONDecodeError) as error:
            raise OllamaError(f"Ollama is unavailable at {self.base_url}. Start Ollama and retry.") from error
        return [item["name"] for item in data.get("models", []) if item.get("name")]

    def stream_chat(
        self, model: str, messages: Sequence[ChatMessage], cancel: Event | None = None
    ) -> Iterator[str]:
        payload = {
            "model": model,
            "stream": True,
            "messages": [
                {"role": "system", "content": self.system_prompt},
                *({"role": message.role, "content": message.content} for message in messages),
            ],
        }
        request = Request(
            f"{self.base_url}/api/chat",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=120) as response:
                for raw_line in response:
                    if cancel and cancel.is_set():
                        break
                    if not raw_line.strip():
                        continue
                    chunk = json.loads(raw_line)
                    if chunk.get("error"):
                        raise OllamaError(chunk["error"])
                    content = chunk.get("message", {}).get("content", "")
                    if content:
                        yield content
        except HTTPError as error:
            message = error.read().decode("utf-8", errors="replace")
            raise OllamaError(f"Ollama request failed ({error.code}): {message}") from error
        except (OSError, URLError, json.JSONDecodeError) as error:
            raise OllamaError(f"Could not read the Ollama response: {error}") from error
