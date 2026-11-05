"""Milestone 2 dashboard and navigation."""

from __future__ import annotations

import shutil
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QFrame, QHBoxLayout, QLabel, QLineEdit, QListWidget, QMainWindow, QMessageBox, QPushButton,
    QStackedWidget, QTextEdit, QVBoxLayout, QWidget,
)

from skywalker.core.config import Settings
from skywalker.domain.ai import ChatMessage
from skywalker.infrastructure.ollama import OllamaProvider
from skywalker.infrastructure.conversation_store import ConversationStore
from skywalker.presentation.ai_worker import ChatWorker, ModelDiscoveryWorker
from skywalker.presentation.styles import STYLE
from skywalker.presentation.activity import ActivityPanel
from skywalker.presentation.assistant_core import AssistantCore
from skywalker.presentation.microphone_worker import MicrophoneWorker
from skywalker.presentation.speech_worker import SpeechWorker
from skywalker.presentation.wake_worker import WakeWordWorker
from skywalker.presentation.automation import ToolsPage, MonitorPage

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
        self.resize(1280, 850)
        self.setMinimumSize(960, 740)
        self.setStyleSheet(STYLE)
        self.settings = Settings.from_environment()
        self.store = ConversationStore(self.settings.database_path)
        self.conversation_id: int | None = None
        self.provider = OllamaProvider(self.settings)
        self.messages: list[ChatMessage] = []
        self.microphone_worker: MicrophoneWorker | None = None
        self.chat_worker: ChatWorker | None = None
        self.discovery_worker: ModelDiscoveryWorker | None = None
        self.speech_worker: SpeechWorker | None = None
        self.wake_worker: WakeWordWorker | None = None
        self.pending_wake_command = ""
        self.wake_detected_flag = False

        root = QWidget()
        self.setCentralWidget(root)
        outer = QHBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(196)
        navigation = QVBoxLayout(sidebar)
        navigation.setContentsMargins(18, 28, 18, 22)
        navigation.setSpacing(9)
        brand = QLabel("Sky Walker")
        brand.setObjectName("brand")
        navigation.addWidget(brand)
        navigation.addWidget(QLabel("Your personal AI"))
        navigation.addSpacing(24)
        self.buttons: list[QPushButton] = []
        for index, name in enumerate(PAGES):
            button = QPushButton(name)
            button.setProperty("nav", True)
            button.clicked.connect(lambda checked=False, page=index: self.select_page(page))
            navigation.addWidget(button)
            self.buttons.append(button)
        navigation.addStretch()
        self.activity = ActivityPanel()
        navigation.addWidget(self.activity)
        navigation.addWidget(QLabel("Local desktop"))
        outer.addWidget(sidebar)

        self.stack = QStackedWidget()
        self.stack.addWidget(self._dashboard())
        self.tools_page = ToolsPage(self.settings.data_directory)
        self.monitor_page = MonitorPage(self.settings.data_directory)
        self.monitor_page.sampled.connect(self.show_metrics)
        for name in PAGES[1:]:
            if name == "Tools":
                page = self.tools_page
            elif name == "System Monitor":
                page = self.monitor_page
            else:
                page = self._conversations() if name == "Conversations" else self._section(name)
            self.stack.addWidget(page)
        outer.addWidget(self.stack, 1)
        self.select_page(0)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_storage)
        self.timer.start(10_000)
        self.refresh_storage()
        self.discover_models()
        self.monitor_page.refresh()

    def _dashboard(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(28, 24, 28, 22)
        layout.setSpacing(16)
        header = QHBoxLayout()
        title = QLabel("Command center")
        title.setObjectName("title")
        header.addWidget(title)
        header.addStretch()
        badge = QLabel("Local workspace")
        badge.setObjectName("badge")
        header.addWidget(badge)
        layout.addLayout(header)
        self.runtime_status = QLabel("Checking local Ollama runtime…")
        self.runtime_status.setObjectName("subtle")
        self.runtime_status.setWordWrap(True)
        layout.addWidget(self.runtime_status)

        body = QHBoxLayout()
        body.setSpacing(16)
        conversation = QFrame()
        conversation.setObjectName("panel")
        chat = QVBoxLayout(conversation)
        chat.setContentsMargins(22, 20, 22, 20)
        chat.setSpacing(14)
        heading = QHBoxLayout()
        label = QLabel("Conversation")
        label.setObjectName("sectionTitle")
        heading.addWidget(label)
        heading.addStretch()
        new_chat = QPushButton("New chat")
        new_chat.clicked.connect(self.new_conversation)
        new_chat.setToolTip("Start a new conversation")
        heading.addWidget(new_chat)
        chat.addLayout(heading)
        model_row = QHBoxLayout()
        model_row.addWidget(QLabel("Model"))
        self.model_selector = QComboBox()
        self.model_selector.setAccessibleName("Local AI model")
        self.model_selector.currentTextChanged.connect(self.model_changed)
        model_row.addWidget(self.model_selector, 1)
        chat.addLayout(model_row)
        self.history = QTextEdit()
        self.history.setObjectName("chatHistory")
        self.history.setAccessibleName("Conversation history")
        self.history.setReadOnly(True)
        self.history.setPlainText("Checking local Ollama runtime and installed models…")
        chat.addWidget(self.history, 1)
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("Type a message, or record your voice…")
        self.chat_input.setAccessibleName("Message to Sky Walker")
        self.chat_input.returnPressed.connect(self.send_message)
        self.chat_input.setDisabled(True)
        chat.addWidget(self.chat_input)
        entry = QHBoxLayout()
        hint = QLabel("Enter to send")
        hint.setObjectName("subtle")
        entry.addWidget(hint)
        entry.addStretch()
        self.stop_button = QPushButton("Stop")
        self.stop_button.setObjectName("danger")
        self.stop_button.clicked.connect(self.stop_generation)
        self.stop_button.setDisabled(True)
        entry.addWidget(self.stop_button)
        self.send_button = QPushButton("Send message")
        self.send_button.setObjectName("primary")
        self.send_button.clicked.connect(self.send_message)
        self.send_button.setDisabled(True)
        entry.addWidget(self.send_button)
        chat.addLayout(entry)
        body.addWidget(conversation, 1)

        voice = QFrame()
        voice.setObjectName("voicePanel")
        voice.setFixedWidth(236)
        controls = QVBoxLayout(voice)
        controls.setContentsMargins(18, 18, 18, 18)
        controls.setSpacing(10)
        label = QLabel("Voice companion")
        label.setObjectName("sectionTitle")
        controls.addWidget(label)
        self.assistant_core = AssistantCore()
        self.activity.changed.connect(self.assistant_core.set_state)
        controls.addWidget(self.assistant_core)
        self.voice_status = QLabel("Microphone idle. Record your voice to compose a message.")
        self.voice_status.setObjectName("subtle")
        self.voice_status.setWordWrap(True)
        self.voice_status.setMinimumHeight(62)
        controls.addWidget(self.voice_status)
        self.microphone_button = QPushButton("Record voice")
        self.microphone_button.clicked.connect(self.record_microphone)
        controls.addWidget(self.microphone_button)
        delete_clip = QPushButton("Delete recording")
        delete_clip.clicked.connect(self.delete_recording)
        controls.addWidget(delete_clip)
        self.speak_replies = QCheckBox("Speak replies")
        self.speak_replies.setChecked(True)
        controls.addWidget(self.speak_replies)
        animate = QCheckBox("Animate activity")
        animate.setChecked(True)
        animate.toggled.connect(self.assistant_core.set_animation)
        controls.addWidget(animate)
        self.wake_toggle = QCheckBox("Hey Sky • deferred")
        self.wake_toggle.setEnabled(False)
        self.wake_toggle.setToolTip("Use Record voice. Wake detection is deferred.")
        self.wake_toggle.toggled.connect(self.toggle_wake_listener)
        controls.addWidget(self.wake_toggle)
        controls.addStretch()
        body.addWidget(voice)
        layout.addLayout(body, 1)

        metrics = QHBoxLayout()
        metrics.setSpacing(12)
        self.metric_labels = {}
        for name in ("CPU", "RAM", "Storage", "Battery"):
            card = QFrame()
            card.setObjectName("metricCard")
            box = QVBoxLayout(card)
            box.setContentsMargins(14, 12, 14, 12)
            caption = QLabel(name)
            caption.setObjectName("subtle")
            box.addWidget(caption)
            value = QLabel("Waiting for sample…")
            value.setObjectName("metric")
            value.setWordWrap(True)
            value.setMinimumHeight(40)
            box.addWidget(value)
            self.metric_labels[name] = value
            metrics.addWidget(card, 1)
        self.storage_label = self.metric_labels["Storage"]
        layout.addLayout(metrics)
        return page

    def show_metrics(self, values: dict[str, str]) -> None:
        for name, label in self.metric_labels.items():
            label.setText(values.get(name, "Unavailable"))

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
        self.activity.set_state("Runtime", "Checking…", busy=True)
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
        self.activity.set_state("Runtime", "Available • checked at startup")
        self.runtime_status.setText(
            f"Ollama online  •  selected model: {self.model_selector.currentText()}"
        )
        self.chat_input.setEnabled(True)
        self.send_button.setEnabled(True)
        if not self.messages:
            self.history.setPlainText("Local model ready. Ask a question to start.")

    def runtime_failed(self, message: str) -> None:
        self.activity.set_state("Runtime", "Unavailable", error=True)
        self.runtime_status.setText("Ollama offline")
        self.history.setPlainText(f"{message}\n\nStart Ollama and choose an installed model, then restart Sky Walker.")
        self.chat_input.setDisabled(True)
        self.send_button.setDisabled(True)

    def send_message(self) -> None:
        if self.microphone_worker and self.microphone_worker.isRunning():
            return
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
        self.activity.set_state("Chat", "Waiting for model…", busy=True)
        self.chat_worker = ChatWorker(self.provider, model, self.messages)
        self.chat_worker.token.connect(self.chat_token)
        self.chat_worker.failed.connect(self.chat_failed)
        self.chat_worker.finished.connect(self.chat_finished)
        self.chat_worker.start()

    def chat_failed(self, message: str) -> None:
        self.activity.set_state("Chat", "Reply failed", error=True)
        self.history.append(f"\n[Ollama error: {message}]")

    def chat_finished(self) -> None:
        if self.activity.states["Chat"] != "Reply failed":
            stopped = self.chat_worker and self.chat_worker.cancel.is_set()
            self.activity.set_state("Chat", "Stopped" if stopped else "Reply complete")
        if self.chat_worker and self.chat_worker.response:
            self.messages.append(ChatMessage("assistant", self.chat_worker.response))
            try:
                self.store.append(self.conversation_id, self.messages[-1])
            except Exception as error:
                QMessageBox.critical(self, "Could not save response", str(error))
            if self.speak_replies.isChecked() and not self.chat_worker.cancel.is_set():
                self.start_speech(self.chat_worker.response)
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
            self.activity.set_state("Chat", "Stopping…", busy=True)
        if self.speech_worker and self.speech_worker.isRunning():
            self.speech_worker.cancel.set()
            self.activity.set_state("Chat", "Stopping speech…", busy=True)

    def start_speech(self, text: str) -> None:
        self.speech_worker = SpeechWorker(text)
        self.speech_worker.speaking.connect(self.speech_started)
        self.speech_worker.finished_speech.connect(self.speech_finished)
        self.speech_worker.failed.connect(self.speech_failed)
        self.stop_button.setEnabled(True)
        self.stop_button.setText("Stop speech")
        self.speech_worker.start()

    def speech_started(self) -> None:
        self.activity.set_state("Chat", "Speaking • local voice", busy=True)

    def speech_finished(self, completed: bool) -> None:
        self.activity.set_state("Chat", "Speech complete" if completed else "Speech stopped")
        self.stop_button.setDisabled(True)
        self.stop_button.setText("Stop")

    def speech_failed(self, message: str) -> None:
        self.activity.set_state("Chat", "Speech failed", error=True)
        self.voice_status.setText(message)
        self.stop_button.setDisabled(True)
        self.stop_button.setText("Stop")

    def chat_token(self, text: str) -> None:
        if not self.chat_worker or not self.chat_worker.cancel.is_set():
            self.activity.set_state("Chat", "Writing reply…", busy=True)
        self.history.insertPlainText(text)

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

    def record_microphone(self) -> None:
        if self.microphone_worker and self.microphone_worker.isRunning():
            if not self.microphone_worker.capture_finished:
                self.microphone_worker.finish_capture.set()
                self.voice_status.setText("Finishing recording…")
                return
            self.microphone_worker.cancel.set()
            self.voice_status.setText("Cancelling recording…")
            self.activity.set_state("Microphone", "Cancelling…", busy=True)
            return
        if self.wake_worker and self.wake_worker.isRunning():
            self.wake_toggle.setChecked(False)
            QTimer.singleShot(150, self.record_microphone)
            return
        self.microphone_worker = MicrophoneWorker(self.settings.data_directory / "audio" / "clip.wav")
        self.microphone_worker.recording.connect(self.recording_started)
        self.microphone_worker.captured.connect(self.transcription_started)
        self.microphone_worker.transcript_ready.connect(self.transcript_ready)
        self.microphone_worker.transcript_preview.connect(self.voice_preview)
        self.microphone_worker.failed.connect(self.voice_failed)
        self.microphone_worker.finished.connect(self.voice_finished)
        self.microphone_button.setText("Finish recording")
        self.chat_input.setReadOnly(True)
        self.voice_status.setText("Opening microphone…")
        self.activity.set_state("Microphone", "Opening…", busy=True)
        self.microphone_worker.start()

    def transcript_ready(self, text: str) -> None:
        self.activity.set_state("Microphone", "Text ready" if text else "No speech detected")
        self.chat_input.setText(text)
        self.voice_status.setText("Review the text, then press Send." if text else "No speech detected.")

    def voice_preview(self, text: str) -> None:
        if self.microphone_worker and not self.microphone_worker.capture_finished:
            self.chat_input.setText(text)
            self.voice_status.setText("Recording • live transcription may lag behind your speech.")

    def recording_started(self) -> None:
        if self.microphone_worker and not self.microphone_worker.cancel.is_set():
            self.activity.set_state("Microphone", "Recording • up to 15 seconds", busy=True)
            self.voice_status.setText("Recording now. Speak into your microphone.")

    def transcription_started(self, path: str) -> None:
        self.microphone_button.setText("Cancel transcription")
        if self.microphone_worker and not self.microphone_worker.cancel.is_set():
            self.activity.set_state("Microphone", "Transcribing • mic off", busy=True)
            self.voice_status.setText("Microphone off. Transcribing locally…")

    def voice_failed(self, message: str) -> None:
        self.activity.set_state("Microphone", "Voice input failed", error=True)
        self.voice_status.setText(message)

    def voice_finished(self) -> None:
        self.microphone_button.setText("Record voice")
        self.chat_input.setReadOnly(False)
        if self.microphone_worker and self.microphone_worker.cancel.is_set():
            self.activity.set_state("Microphone", "Cancelled • mic off")
            self.voice_status.setText("Voice input cancelled. Microphone off.")

    def toggle_wake_listener(self, enabled: bool) -> None:
        if enabled:
            if self.microphone_worker and self.microphone_worker.isRunning():
                self.wake_toggle.setChecked(False)
                self.voice_status.setText("Finish voice input before starting the wake listener.")
                return
            if self.wake_worker and self.wake_worker.isRunning():
                return
            self.wake_worker = WakeWordWorker()
            self.wake_worker.listening.connect(self.wake_listening)
            self.wake_worker.detected.connect(self.wake_detected)
            self.wake_worker.failed.connect(self.wake_failed)
            self.wake_worker.finished.connect(self.wake_finished)
            self.wake_toggle.setText("Listening for Hey Sky…")
            self.activity.set_state("Microphone", "Starting wake listener…", busy=True)
            self.wake_worker.start()
        elif self.wake_worker and self.wake_worker.isRunning():
            self.wake_worker.cancel.set()
            self.activity.set_state("Microphone", "Stopping wake listener…", busy=True)

    def wake_listening(self) -> None:
        self.wake_toggle.setText("Listening for Hey Sky • experimental")
        self.activity.set_state("Microphone", "Listening for Hey Sky", busy=True)
        self.voice_status.setText("Microphone active. Speech is checked locally to detect the phrase.")

    def wake_detected(self, command: str) -> None:
        self.pending_wake_command = command
        self.wake_detected_flag = True
        self.activity.set_state("Microphone", "Hey Sky detected")
        self.wake_toggle.setChecked(False)
        self.voice_status.setText("Wake phrase detected. Preparing voice input…")

    def wake_failed(self, message: str) -> None:
        self.activity.set_state("Microphone", "Wake listener failed", error=True)
        self.voice_status.setText(message)
        self.wake_toggle.setChecked(False)

    def wake_finished(self) -> None:
        self.wake_toggle.setText("Listen for Hey Sky (experimental)")
        detected = self.wake_detected_flag
        self.wake_detected_flag = False
        if self.pending_wake_command:
            self.chat_input.setText(self.pending_wake_command)
            self.pending_wake_command = ""
            self.voice_status.setText("Hey Sky detected. Review the text, then press Send.")
        elif detected:
            if self.model_selector.currentText():
                QTimer.singleShot(150, self.record_microphone)
            else:
                self.voice_status.setText("Wake phrase detected. Start Ollama to continue.")
        else:
            if self.activity.states["Microphone"] != "Wake listener failed":
                self.activity.set_state("Microphone", "Wake listener off")
                self.voice_status.setText("Wake listener off. Microphone idle.")

    def delete_recording(self) -> None:
        if self.microphone_worker and self.microphone_worker.isRunning():
            self.voice_status.setText("Cancel recording before deleting it.")
            return
        try:
            (self.settings.data_directory / "audio" / "clip.wav").unlink(missing_ok=True)
            self.voice_status.setText("Recording deleted.")
        except OSError as error:
            self.voice_status.setText(f"Could not delete recording: {error}")

    def closeEvent(self, event) -> None:
        if self.tools_page.worker and self.tools_page.worker.isRunning():
            self.tools_page.stop()
            self.statusBar().showMessage("Stopping tool operation. Close again when it finishes.")
            event.ignore()
            return
        workers = [self.chat_worker, self.discovery_worker, self.microphone_worker, self.speech_worker, self.wake_worker]
        if any(worker and worker.isRunning() for worker in workers):
            if self.microphone_worker and self.microphone_worker.isRunning():
                self.microphone_worker.cancel.set()
            if self.speech_worker and self.speech_worker.isRunning():
                self.speech_worker.cancel.set()
            if self.wake_worker and self.wake_worker.isRunning():
                self.wake_worker.cancel.set()
            self.statusBar().showMessage("Wait for active work to finish before closing.")
            event.ignore()
            return
        event.accept()
