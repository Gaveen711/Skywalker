"""Provider independent conversation types and interface."""

from __future__ import annotations

from dataclasses import dataclass
from threading import Event
from typing import Iterator, Protocol, Sequence


@dataclass(frozen=True, slots=True)
class ChatMessage:
    role: str
    content: str


class AIProvider(Protocol):
    def list_models(self) -> list[str]: ...

    def stream_chat(
        self, model: str, messages: Sequence[ChatMessage], cancel: Event | None = None
    ) -> Iterator[str]: ...
