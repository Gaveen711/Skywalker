"""Offline transcription using a verified local whisper.cpp executable."""

import os
import subprocess
import tempfile
import wave
from array import array
from pathlib import Path


def transcribe(clip: Path) -> str:
    root = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "SkyWalker"
    executable = root / "runtimes" / "whisper-b5454" / "Release" / "whisper-cli.exe"
    model = root / "models" / "ggml-small.en.bin"
    if not executable.is_file() or not model.is_file():
        raise RuntimeError("Local Whisper runtime or English model is missing.")
    with wave.open(str(clip), "rb") as source:
        if source.getnchannels() != 1 or source.getsampwidth() != 2:
            raise ValueError("Transcription requires mono 16-bit PCM audio.")
        rate = source.getframerate()
        samples = array("h", source.readframes(source.getnframes()))
    if not samples:
        return ""
    if rate != 16000:
        raise ValueError("Please record again using 16 kHz audio.")
    # Preserve the device's 16 kHz PCM samples without a lossy resampling step.
    converted = samples
    with tempfile.TemporaryDirectory(prefix="transcription-", dir=clip.parent) as temporary:
        audio = Path(temporary) / "input.wav"
        output = Path(temporary) / "result"
        with wave.open(str(audio), "wb") as target:
            target.setnchannels(1)
            target.setsampwidth(2)
            target.setframerate(16000)
            target.writeframes(converted.tobytes())
        result = subprocess.run(
            [str(executable), "-m", str(model), "-f", str(audio), "-l", "en",
             "-otxt", "-of", str(output), "-t", "4"],
            capture_output=True, timeout=180, creationflags=subprocess.CREATE_NO_WINDOW,
        )
        if result.returncode:
            raise RuntimeError("Local transcription failed. Check the Whisper runtime and model.")
        transcript = output.with_suffix(".txt")
        if not transcript.is_file():
            raise RuntimeError("Whisper did not produce a transcript.")
        return transcript.read_text(encoding="utf-8").strip()
