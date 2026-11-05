"""Bounded, user initiated microphone capture to a local WAV file."""

from __future__ import annotations

import wave
from collections.abc import Callable
from pathlib import Path
from threading import Event


def record_clip(destination: Path, cancel: Event, seconds: int = 15,
                on_started: Callable[[], None] | None = None,
                finish: Event | None = None,
                on_progress: Callable[[bytes], None] | None = None) -> Path:
    """Record mono PCM at the device's supported default rate."""
    import sounddevice as sd

    rate = 16000
    sd.check_input_settings(channels=1, dtype="int16", samplerate=rate)
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        with sd.RawInputStream(samplerate=rate, channels=1, dtype="int16") as stream:
            if on_started:
                on_started()
            with wave.open(str(destination), "wb") as output:
                output.setnchannels(1)
                output.setsampwidth(2)
                output.setframerate(rate)
                remaining = rate * seconds
                samples = bytearray()
                next_update = rate * 3 * 2
                while remaining > 0 and not cancel.is_set() and not (finish and finish.is_set()):
                    count = min(1024, remaining)
                    data, overflow = stream.read(count)
                    if overflow:
                        raise RuntimeError("Microphone input overflowed. Please record again.")
                    output.writeframes(bytes(data))
                    if on_progress:
                        samples.extend(data)
                        if len(samples) >= next_update:
                            on_progress(bytes(samples))
                            next_update += rate * 3 * 2
                    remaining -= count
        if cancel.is_set():
            destination.unlink(missing_ok=True)
        return destination
    except Exception:
        destination.unlink(missing_ok=True)
        raise
