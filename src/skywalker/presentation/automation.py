"""User-controlled tools and native system monitoring pages."""
from pathlib import Path

from PySide6.QtCore import QThread, QTimer, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox,
    QLineEdit, QPlainTextEdit, QFileDialog, QMessageBox,
)

from skywalker.infrastructure.system_monitor import SystemMonitor
from skywalker.tools.executor import APPLICATIONS, ToolExecutor
from skywalker.tools.registry import TOOLS


class ToolWorker(QThread):
    result = Signal(str)

    def __init__(self, executor: ToolExecutor, arguments: tuple, confirmed: bool) -> None:
        super().__init__()
        self.executor = executor
        self.arguments = arguments
        self.confirmed = confirmed

    def run(self) -> None:
        try:
            self.result.emit(self.executor.execute(*self.arguments, confirmed=self.confirmed))
        except Exception as error:
            self.result.emit(f"Operation failed: {error}")


class ToolsPage(QWidget):
    def __init__(self, data: Path) -> None:
        super().__init__()
        self.executor = ToolExecutor(data / "logs" / "tools.jsonl")
        self.worker: ToolWorker | None = None
        self.root: Path | None = None
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Computer tools"))
        note = QLabel("Choose an operation yourself. File contents stay in this view and are not sent to the AI.")
        note.setWordWrap(True)
        layout.addWidget(note)
        self.folder = QLabel("No folder approved • permission lasts until you close the app")
        self.folder.setWordWrap(True)
        layout.addWidget(self.folder)
        row = QHBoxLayout()
        self.approve = QPushButton("Approve folder")
        self.approve.clicked.connect(self.choose_folder)
        self.revoke = QPushButton("Revoke folder")
        self.revoke.clicked.connect(self.revoke_folder)
        row.addWidget(self.approve)
        row.addWidget(self.revoke)
        layout.addLayout(row)
        self.operation = QComboBox()
        for key, tool in TOOLS.items():
            self.operation.addItem(tool.label, key)
        layout.addWidget(self.operation)
        self.application = QComboBox()
        self.application.addItems(list(APPLICATIONS))
        layout.addWidget(self.application)
        self.source = QLineEdit()
        self.source.setPlaceholderText("Relative file path, or part of a filename for search")
        layout.addWidget(self.source)
        self.destination = QLineEdit()
        self.destination.setPlaceholderText("New relative file path for copy • existing files are never overwritten")
        layout.addWidget(self.destination)
        self.operation.currentIndexChanged.connect(self.update_fields)
        self.update_fields()
        row = QHBoxLayout()
        self.run_button = QPushButton("Run selected tool")
        self.run_button.clicked.connect(self.execute)
        row.addWidget(self.run_button)
        stop = QPushButton("EMERGENCY STOP")
        stop.clicked.connect(self.stop)
        row.addWidget(stop)
        self.resume = QPushButton("Resume tools")
        self.resume.clicked.connect(self.resume_tools)
        row.addWidget(self.resume)
        layout.addLayout(row)
        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        self.output.setPlaceholderText("Results and file previews appear here.")
        layout.addWidget(self.output, 1)

    def update_fields(self) -> None:
        key = self.operation.currentData()
        self.application.setVisible(key == "launch")
        self.source.setVisible(key != "launch")
        self.destination.setVisible(key == "copy")

    def choose_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Approve a folder for file tools")
        if folder:
            self.root = Path(folder)
            self.folder.setText(f"Approved for this session: {folder}")

    def revoke_folder(self) -> None:
        self.root = None
        self.folder.setText("No folder approved")
        self.output.clear()

    def execute(self) -> None:
        if self.worker and self.worker.isRunning():
            return
        key = self.operation.currentData()
        source = self.application.currentText() if key == "launch" else self.source.text().strip()
        destination = self.destination.text().strip()
        confirmed = False
        if TOOLS[key].confirmation:
            detail = f"Open {source}?" if key == "launch" else f"Copy {source}\nto {destination}\nwithin {self.root}?"
            confirmed = QMessageBox.question(self, "Confirm operation", detail) == QMessageBox.StandardButton.Yes
            if not confirmed:
                return
        self.worker = ToolWorker(self.executor, (key, self.root, source, destination), confirmed)
        self.worker.result.connect(self.output.setPlainText)
        self.worker.finished.connect(self.finished)
        self.run_button.setEnabled(False)
        self.approve.setEnabled(False)
        self.revoke.setEnabled(False)
        self.output.setPlainText("Working…")
        self.worker.start()

    def finished(self) -> None:
        self.run_button.setEnabled(not self.executor.cancel.is_set())
        self.approve.setEnabled(True)
        self.revoke.setEnabled(True)

    def stop(self) -> None:
        self.executor.cancel.set()
        self.run_button.setEnabled(False)
        self.output.setPlainText("Emergency stop active. Running work will stop at its next checkpoint. Already opened apps remain open.")

    def resume_tools(self) -> None:
        if self.worker and self.worker.isRunning():
            return
        self.executor.cancel.clear()
        self.run_button.setEnabled(True)
        self.output.setPlainText("Tools ready.")


class MonitorPage(QWidget):
    sampled = Signal(dict)

    def __init__(self, data: Path) -> None:
        super().__init__()
        self.monitor = SystemMonitor(Path(data.anchor))
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("System monitor • updates every 3 seconds"))
        self.labels = {}
        for key in ("System", "CPU", "RAM", "Storage", "Battery"):
            label = QLabel(f"{key}: waiting for sample…")
            layout.addWidget(label)
            self.labels[key] = label
        layout.addStretch()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(3000)

    def refresh(self) -> None:
        try:
            values = self.monitor.sample()
            for key, value in values.items():
                self.labels[key].setText(f"{key}: {value}")
            self.sampled.emit(values)
        except Exception as error:
            for label in self.labels.values():
                label.setText(f"Monitoring unavailable: {error}")
