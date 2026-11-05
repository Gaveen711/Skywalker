"""Background workers for model discovery and streamed inference."""

from __future__ import annotations

from collections.abc import Sequence
from threading import Event

from PySide6.QtCore import QThread, Signal

from skywalker.domain.ai import AIProvider, ChatMessage


class ModelDiscoveryWorker(QThread):
    models_ready = Signal(list)
    failed = Signal(str)

    def __init__(self, provider: AIProvider) -> None:
        super().__init__()
        self.provider = provider

    def run(self) -> None:
        try:
            self.models_ready.emit(self.provider.list_models())
        except Exception as error:
            self.failed.emit(str(error))


class ChatWorker(QThread):
    token = Signal(str)
    failed = Signal(str)

    def __init__(self, provider: AIProvider, model: str, messages: Sequence[ChatMessage]) -> None:
        super().__init__()
        self.provider = provider
        self.model = model
        self.messages = tuple(messages)
        self.cancel = Event()
        self.response = ""

    def run(self) -> None:
        try:
            for piece in self.provider.stream_chat(self.model, self.messages, self.cancel):
                if self.cancel.is_set():
                    break
                self.response += piece
                self.token.emit(piece)
        except Exception as error:
            self.failed.emit(str(error))
