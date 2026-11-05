"""Activity visualization driven by worker states; animation stops when idle or hidden."""
from PySide6.QtCore import QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QRadialGradient
from PySide6.QtWidgets import QWidget


class AssistantCore(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setMinimumSize(170, 174)
        self.setMaximumHeight(210)
        self.states = {}
        self.phase = 0
        self.active = False
        self.animate = True
        self.state = "Idle"
        self.color = QColor("#5bd8ed")
        self.timer = QTimer(self)
        self.timer.setInterval(80)
        self.timer.timeout.connect(self.advance)
        self.setAccessibleName("Assistant idle")

    def advance(self) -> None:
        self.phase = (self.phase + 3) % 360
        self.update()

    def set_animation(self, enabled: bool) -> None:
        self.animate = enabled
        self.sync_timer()

    def sync_timer(self) -> None:
        if self.active and self.animate and self.isVisible():
            self.timer.start()
        else:
            self.timer.stop()

    def showEvent(self, event) -> None:
        self.sync_timer()
        super().showEvent(event)

    def hideEvent(self, event) -> None:
        self.timer.stop()
        super().hideEvent(event)

    def set_state(self, lane: str, state: str, busy: bool, error: bool) -> None:
        self.states[lane] = (state, busy, error)
        self.active = any(value[1] for value in self.states.values())
        current = next((value[0] for key, value in self.states.items()
                        if key == "Microphone" and value[1]), "")
        current = current or next((value[0] for value in self.states.values() if value[1]), "")
        if current:
            word = current.lower()
            self.state = "Listening" if "recording" in word else "Speaking" if "speaking" in word else "Processing"
            self.color = QColor("#b6a4fa" if self.state == "Speaking" else "#5bd8ed")
        elif any(value[2] for value in self.states.values()):
            self.state, self.color = "Needs attention", QColor("#f2ab91")
        else:
            self.state, self.color = "Idle", QColor("#5bd8ed")
        self.setAccessibleName(f"Assistant {self.state.lower()}")
        self.sync_timer()
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        center = self.rect().center()
        painter.translate(center.x(), center.y() - 12)
        radius = min(self.width() / 2 - 12, self.height() / 2 - 24)
        gradient = QRadialGradient(0, 0, radius)
        tint = QColor(self.color)
        tint.setAlpha(40)
        gradient.setColorAt(0, tint)
        gradient.setColorAt(1, QColor(9, 18, 31, 0))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(gradient)
        painter.drawEllipse(QRectF(-radius, -radius, radius * 2, radius * 2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(QColor("#243d52"), 1))
        painter.drawEllipse(QRectF(-radius, -radius, radius * 2, radius * 2))
        painter.save()
        painter.rotate(self.phase)
        painter.setPen(QPen(self.color, 2))
        for start in (25, 145, 265):
            painter.drawArc(QRectF(-radius + 7, -radius + 7, radius * 2 - 14, radius * 2 - 14), start * 16, 65 * 16)
        painter.restore()
        painter.setPen(QPen(QColor("#356078"), 1))
        painter.drawEllipse(QRectF(-radius * .65, -radius * .65, radius * 1.3, radius * 1.3))
        painter.setPen(self.color)
        painter.setFont(QFont("Segoe UI", 25, QFont.Weight.Light))
        painter.drawText(QRectF(-50, -30, 100, 60), Qt.AlignmentFlag.AlignCenter, "S")
        painter.setFont(QFont("Segoe UI", 10))
        painter.drawText(QRectF(-100, radius + 8, 200, 25), Qt.AlignmentFlag.AlignCenter, self.state)
