"""Qt microphone capture worker."""

from pathlib import Path
from threading import Event
from concurrent.futures import ThreadPoolExecutor
import tempfile
import wave

from PySide6.QtCore import QThread, Signal

from skywalker.infrastructure.microphone import record_clip
from skywalker.infrastructure.transcription import transcribe


class MicrophoneWorker(QThread):
    recording = Signal()
    captured = Signal(str)
    failed = Signal(str)
    transcript_ready = Signal(str)
    transcript_preview = Signal(str)

    def __init__(self, destination: Path) -> None:
        super().__init__()
        self.destination = destination
        self.cancel = Event()
        self.finish_capture = Event()
        self.capture_finished = False

    def run(self) -> None:
        try:
            recording_done = Event()
            with ThreadPoolExecutor(max_workers=1) as executor:
                pending = None

                def preview(audio: bytes) -> None:
                    nonlocal pending
                    if pending is not None and not pending.done():
                        return

                    def generate() -> None:
                        try:
                            with tempfile.TemporaryDirectory(prefix="sky-preview-") as folder:
                                clip = Path(folder) / "preview.wav"
                                with wave.open(str(clip), "wb") as wav:
                                    wav.setnchannels(1)
                                    wav.setsampwidth(2)
                                    wav.setframerate(16000)
                                    wav.writeframes(audio)
                                text = transcribe(clip)
                            if text and not recording_done.is_set() and not self.cancel.is_set():
                                self.transcript_preview.emit(text)
                        except Exception:
                            # The final transcription reports errors to the user.
                            pass

                    pending = executor.submit(generate)

                try:
                    record_clip(self.destination, self.cancel, on_started=self.recording.emit,
                                finish=self.finish_capture, on_progress=preview)
                    self.capture_finished = True
                    if not self.cancel.is_set():
                        self.captured.emit(str(self.destination))
                finally:
                    recording_done.set()
            if not self.cancel.is_set():
                text = transcribe(self.destination)
                if not self.cancel.is_set():
                    self.transcript_ready.emit(text)
        except Exception as error:
            self.failed.emit(f"Voice input failed: {error}")
