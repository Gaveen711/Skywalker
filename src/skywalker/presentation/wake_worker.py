"""Opt-in spoken-phrase wake listener built on local Whisper transcription."""

from __future__ import annotations

import math
import tempfile
import wave
from array import array
from collections import deque
from pathlib import Path
from threading import Event

from PySide6.QtCore import QThread, Signal

from skywalker.infrastructure.transcription import transcribe


def extract_wake_command(phrase: str) -> str | None:
    """Return words after a spoken 'Hey Sky', or None when it was not heard."""
    normalized = " ".join("".join(c if c.isalnum() else " " for c in phrase.lower()).split())
    words = normalized.split()
    for index in range(len(words) - 1):
        if words[index:index + 2] == ["hey", "sky"]:
            return " ".join(words[index + 2:])
    return None


class WakeWordWorker(QThread):
    detected = Signal(str)
    listening = Signal()
    failed = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.cancel = Event()

    def run(self) -> None:
        import sounddevice as sd

        rate = 16000
        block = 4000
        try:
            sd.check_input_settings(channels=1, dtype="int16", samplerate=rate)
            with sd.RawInputStream(samplerate=rate, channels=1, dtype="int16", blocksize=block) as stream:
                self.listening.emit()
                audio = bytearray()
                quiet = 0
                voice_frames = 0
                pre_roll = deque(maxlen=2)
                while not self.cancel.is_set():
                    data, overflow = stream.read(block)
                    if overflow:
                        raise RuntimeError("Microphone input overflowed. Try again.")
                    raw = bytes(data)
                    samples = array("h")
                    samples.frombytes(raw)
                    rms = math.sqrt(sum(sample * sample for sample in samples) / max(len(samples), 1))
                    if not audio:
                        if rms < 200:
                            pre_roll.append(raw)
                            continue
                        for previous in pre_roll:
                            audio.extend(previous)
                        pre_roll.clear()
                        audio.extend(raw)
                        voice_frames = 1
                        quiet = 0
                        continue
                    audio.extend(raw)
                    voice_frames += 1
                    quiet = quiet + 1 if rms < 200 else 0
                    if quiet < 4 and voice_frames < 24:
                        continue
                    if voice_frames >= 3:
                        with tempfile.TemporaryDirectory(prefix="sky-wake-") as folder:
                            clip = Path(folder) / "phrase.wav"
                            with wave.open(str(clip), "wb") as wav:
                                wav.setnchannels(1)
                                wav.setsampwidth(2)
                                wav.setframerate(rate)
                                wav.writeframes(audio)
                            phrase = transcribe(clip)
                        command = extract_wake_command(phrase)
                        if command is not None:
                            if not self.cancel.is_set():
                                self.detected.emit(command)
                            return
                    audio.clear()
                    quiet = 0
                    voice_frames = 0
        except Exception as error:
            if not self.cancel.is_set():
                self.failed.emit(f"Hey Sky listener failed: {error}")
