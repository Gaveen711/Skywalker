"""Milestone 2 dashboard and navigation."""

from __future__ import annotations

import shutil
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QComboBox, QFrame, QHBoxLayout, QLabel, QLineEdit, QListWidget, QMainWindow, QMessageBox, QPushButton,
    QStackedWidget, QTextEdit, QVBoxLayout, QWidget,
)

from skywalker.core.config import Settings
from skywalker.domain.ai import ChatMessage
from skywalker.infrastructure.ollama import OllamaProvider
from skywalker.infrastructure.conversation_store import ConversationStore
from skywalker.presentation.ai_worker import ChatWorker, ModelDiscoveryWorker
from skywalker.presentation.styles import STYLE

PAGES = ("Dashboard", "Conversations", "Memory", "Tools", "System Monitor", "Settings")


def panel(title: str, body: str) -> QFrame:
    """Create a small information panel."""
    frame = QFrame()
    frame.setObjectName("panel")
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(20, 18, 20, 18)
    heading = QLabel(title)
    heading.setObjectName("subtle")
    layout.addWidget(heading)
    layout.addWidget(QLabel(body))
    return frame


class MainWindow(QMainWindow):
    """Desktop shell with honest feature and runtime states."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Sky Walker")
        self.resize(1180, 760)
        self.setMinimumSize(900, 600)
        self.setStyleSheet(STYLE)
        self.settings = Settings.from_environment()
        self.store = ConversationStore(self.settings.database_path)
        self.conversation_id: int | None = None
        self.provider = OllamaProvider(self.settings)
        self.messages: list[ChatMessage] = []
        self.chat_worker: ChatWorker | None = None
        self.discovery_worker: ModelDiscoveryWorker | None = None

        root = QWidget()
        self.setCentralWidget(root)
        outer = QHBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(220)
        navigation = QVBoxLayout(sidebar)
        navigation.setContentsMargins(18, 28, 18, 22)
        navigation.setSpacing(9)
        brand = QLabel("SKY WALKER")
        brand.setObjectName("brand")
        navigation.addWidget(brand)
        navigation.addSpacing(34)
        self.buttons: list[QPushButton] = []
        for index, name in enumerate(PAGES):
            button = QPushButton(name)
            button.clicked.connect(lambda checked=False, page=index: self.select_page(page))
            navigation.addWidget(button)
            self.buttons.append(button)
        navigation.addStretch()
        navigation.addWidget(QLabel("Local desktop • Milestone 2"))
        outer.addWidget(sidebar)

        self.stack = QStackedWidget()
        self.stack.addWidget(self._dashboard())
        for name in PAGES[1:]:
            self.stack.addWidget(self._conversations() if name == "Conversations" else self._section(name))
        outer.addWidget(self.stack, 1)
        self.select_page(0)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_storage)
        self.timer.start(10_000)
        self.refresh_storage()
        self.discover_models()

    def _dashboard(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(18)
        title = QLabel("Your command space")
        title.setObjectName("title")
        layout.addWidget(title)
        self.runtime_status = QLabel("Connecting to local Ollama…")
        self.runtime_status.setObjectName("subtle")
        layout.addWidget(self.runtime_status)

        conversation = QFrame()
        conversation.setObjectName("panel")
        chat = QVBoxLayout(conversation)
        chat.setContentsMargins(20, 18, 20, 18)
        chat.addWidget(QLabel("Conversation"))
        self.history = QTextEdit()
        self.history.setReadOnly(True)
        self.history.setPlainText("Checking local Ollama runtime and installed models…")
        chat.addWidget(self.history, 1)
        entry = QHBoxLayout()
        self.model_selector = QComboBox()
        self.model_selector.setMinimumWidth(145)
        entry.addWidget(self.model_selector)
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("Ask your local assistant")
        self.chat_input.returnPressed.connect(self.send_message)
        self.model_selector.currentTextChanged.connect(self.model_changed)
        self.chat_input.setDisabled(True)
        entry.addWidget(self.chat_input, 1)
        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_message)
        self.send_button.setDisabled(True)
        entry.addWidget(self.send_button)
        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.stop_generation)
        self.stop_button.setDisabled(True)
        entry.addWidget(self.stop_button)
        chat.addLayout(entry)
        layout.addWidget(conversation, 1)

        metrics = QHBoxLayout()
        self.storage_label = QLabel("Checking storage…")
        storage = panel("Local storage", "")
        storage.layout().addWidget(self.storage_label)
        metrics.addWidget(storage)
        metrics.addWidget(panel("CPU and memory", "Monitoring arrives in Milestone 6"))
        layout.addLayout(metrics)
        return page

    def _section(self, name: str) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(32, 28, 32, 28)
        title = QLabel(name)
        title.setObjectName("title")
        layout.addWidget(title)
        layout.addWidget(panel("Coming in a later milestone", f"{name} is not active yet."))
        layout.addStretch()
        return page

    def select_page(self, index: int) -> None:
        """Show a navigation page and mark its button selected."""
        self.stack.setCurrentIndex(index)
        for number, button in enumerate(self.buttons):
            button.setObjectName("selected" if number == index else "")
            button.style().unpolish(button)
            button.style().polish(button)
        self.statusBar().showMessage(PAGES[index])

    def refresh_storage(self) -> None:
        """Show real local disk data or a visible error."""
        try:
            root = Path(Settings.from_environment().data_directory.anchor)
            usage = shutil.disk_usage(root)
            free_gb = usage.free / (1024 ** 3)
            total_gb = usage.total / (1024 ** 3)
            self.storage_label.setText(f"{free_gb:.1f} GB free of {total_gb:.1f} GB")
        except OSError as error:
            self.storage_label.setText(f"Storage unavailable: {error.strerror or error}")

    def discover_models(self) -> None:
        self.runtime_status.setText("Checking local Ollama runtime…")
        self.discovery_worker = ModelDiscoveryWorker(self.provider)
        self.discovery_worker.models_ready.connect(self.models_loaded)
        self.discovery_worker.failed.connect(self.runtime_failed)
        self.discovery_worker.start()

    def models_loaded(self, models: list[str]) -> None:
        self.model_selector.clear()
        self.model_selector.addItems(models)
        preferred = self.settings.model_name
        index = self.model_selector.findText(preferred)
        if index >= 0:
            self.model_selector.setCurrentIndex(index)
        if not models:
            self.runtime_failed("Ollama is running, but no local models are installed.")
            return
        self.runtime_status.setText(
            f"Ollama online  •  selected model: {self.model_selector.currentText()}"
        )
        self.chat_input.setEnabled(True)
        self.send_button.setEnabled(True)
        if not self.messages:
            self.history.setPlainText("Local model ready. Ask a question to start.")

    def runtime_failed(self, message: str) -> None:
        self.runtime_status.setText("Ollama offline")
        self.history.setPlainText(f"{message}\n\nStart Ollama and choose an installed model, then restart Sky Walker.")
        self.chat_input.setDisabled(True)
        self.send_button.setDisabled(True)

    def send_message(self) -> None:
        prompt = self.chat_input.text().strip()
        model = self.model_selector.currentText()
        if not prompt or not model or (self.chat_worker and self.chat_worker.isRunning()):
            return
        self.chat_input.clear()
        try:
            if self.conversation_id is None:
                self.conversation_id = self.store.create(prompt)
            self.store.append(self.conversation_id, ChatMessage("user", prompt))
        except Exception as error:
            QMessageBox.critical(self, "Could not save conversation", str(error))
            return
        self.messages.append(ChatMessage("user", prompt))
        self.refresh_conversations()
        self.history.append(f"\nYou: {prompt}\nSky Walker: ")
        self.send_button.setDisabled(True)
        self.stop_button.setEnabled(True)
        self.chat_worker = ChatWorker(self.provider, model, self.messages)
        self.chat_worker.token.connect(self.history.insertPlainText)
        self.chat_worker.failed.connect(self.chat_failed)
        self.chat_worker.finished.connect(self.chat_finished)
        self.chat_worker.start()

    def chat_failed(self, message: str) -> None:
        self.history.append(f"\n[Ollama error: {message}]")

    def chat_finished(self) -> None:
        if self.chat_worker and self.chat_worker.response:
            self.messages.append(ChatMessage("assistant", self.chat_worker.response))
            try:
                self.store.append(self.conversation_id, self.messages[-1])
            except Exception as error:
                QMessageBox.critical(self, "Could not save response", str(error))
        self.stop_button.setDisabled(True)
        self.stop_button.setText("Stop")
        self.send_button.setEnabled(bool(self.model_selector.currentText()))
        self.chat_input.setEnabled(bool(self.model_selector.currentText()))

    def model_changed(self, model: str) -> None:
        if model:
            self.runtime_status.setText(f"Ollama online  •  selected model: {model}")

    def stop_generation(self) -> None:
        # Closing the local HTTP stream is handled by the worker when generation ends.
        if self.chat_worker and self.chat_worker.isRunning():
            self.chat_worker.cancel.set()
            self.stop_button.setText("Stopping…")

    def _conversations(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(QLabel("Saved conversations"))
        self.conversation_list = QListWidget()
        layout.addWidget(self.conversation_list)
        for title, action in (("New conversation", self.new_conversation),
                              ("Open selected", self.open_conversation),
                              ("Delete selected", self.delete_conversation)):
            button = QPushButton(title)
            button.clicked.connect(action)
            layout.addWidget(button)
        self.refresh_conversations()
        return page

    def refresh_conversations(self) -> None:
        self.saved_conversations = self.store.list_conversations()
        self.conversation_list.clear()
        self.conversation_list.addItems([title for _, title in self.saved_conversations])

    def new_conversation(self) -> None:
        if self.chat_worker and self.chat_worker.isRunning():
            return
        self.conversation_id = None
        self.messages = []
        self.history.clear()
        self.select_page(0)

    def open_conversation(self) -> None:
        row = self.conversation_list.currentRow()
        if row < 0 or (self.chat_worker and self.chat_worker.isRunning()):
            return
        self.conversation_id = self.saved_conversations[row][0]
        self.messages = self.store.load(self.conversation_id)
        self.history.setPlainText("\n\n".join(f"{m.role}: {m.content}" for m in self.messages))
        self.select_page(0)

    def delete_conversation(self) -> None:
        row = self.conversation_list.currentRow()
        if row < 0 or (self.chat_worker and self.chat_worker.isRunning()):
            return
        if QMessageBox.question(self, "Delete conversation", "Permanently delete this conversation?") != QMessageBox.StandardButton.Yes:
            return
        identifier = self.saved_conversations[row][0]
        self.store.delete(identifier)
        if identifier == self.conversation_id:
            self.new_conversation()
        self.refresh_conversations()
