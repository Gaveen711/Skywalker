"""Independent, event-driven activity indicators for concurrent operations."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QLabel, QProgressBar, QVBoxLayout


class ActivityPanel(QFrame):
    changed = Signal(str, str, bool, bool)
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("panel")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.addWidget(QLabel("Assistant activity"))
        self.labels: dict[str, QLabel] = {}
        self.busy: dict[str, bool] = {}
        self.states: dict[str, str] = {}
        for lane in ("Runtime", "Chat", "Microphone"):
            label = QLabel()
            label.setWordWrap(True)
            label.setAccessibleName(f"{lane} status")
            layout.addWidget(label)
            self.labels[lane] = label
        self.progress = QProgressBar()
        self.progress.setAccessibleName("Assistant busy")
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(5)
        self.progress.setStyleSheet(
            "QProgressBar { border: 0; background: #163047; }"
            "QProgressBar::chunk { background: #67DDF1; }"
        )
        layout.addWidget(self.progress)
        for lane in self.labels:
            self.set_state(lane, "Idle")

    def set_state(self, lane: str, state: str, *, busy: bool = False, error: bool = False) -> None:
        self.states[lane] = state
        self.busy[lane] = busy
        color = "#FF9999" if error else "#67DDF1" if busy else "#B9CDD9"
        self.labels[lane].setText(f"{lane}: {state}")
        self.labels[lane].setStyleSheet(f"color: {color}; background: transparent;")
        active = any(self.busy.values())
        self.progress.setRange(0, 0 if active else 1)
        self.progress.setVisible(active)
        self.changed.emit(lane, state, busy, error)
