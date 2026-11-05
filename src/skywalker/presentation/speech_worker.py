"""Background spoken-response worker."""

from threading import Event

from PySide6.QtCore import QThread, Signal

from skywalker.infrastructure.speech import speak


class SpeechWorker(QThread):
    speaking = Signal()
    finished_speech = Signal(bool)
    failed = Signal(str)

    def __init__(self, text: str) -> None:
        super().__init__()
        self.text = text
        self.cancel = Event()

    def run(self) -> None:
        try:
            completed = speak(self.text, self.cancel, self.speaking.emit)
            self.finished_speech.emit(completed)
        except Exception as error:
            self.failed.emit(str(error))
