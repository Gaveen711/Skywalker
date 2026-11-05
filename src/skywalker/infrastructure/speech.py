"""Interruptible spoken output through Windows' built-in SAPI voice."""

from __future__ import annotations

import base64
import os
import shutil
import subprocess
import time
from threading import Event
from typing import Callable


_SCRIPT = """
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Speech
$speaker = New-Object System.Speech.Synthesis.SpeechSynthesizer
$text = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($env:SKYWALKER_TTS_TEXT))
$speaker.Speak($text)
$speaker.Dispose()
"""
_ENCODED_SCRIPT = base64.b64encode(_SCRIPT.encode("utf-16le")).decode("ascii")


def speak(text: str, cancel: Event, on_started: Callable[[], None] | None = None) -> bool:
    """Speak text locally; terminate the child promptly when interrupted."""
    executable = shutil.which("powershell.exe")
    if not executable:
        raise RuntimeError("Windows PowerShell is unavailable for speech output.")
    environment = os.environ.copy()
    environment["SKYWALKER_TTS_TEXT"] = base64.b64encode(text.encode("utf-8")).decode("ascii")
    process = subprocess.Popen(
        [executable, "-NoProfile", "-NonInteractive", "-EncodedCommand", _ENCODED_SCRIPT],
        env=environment,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    if on_started:
        on_started()
    try:
        while process.poll() is None:
            if cancel.is_set():
                process.terminate()
                process.wait(timeout=3)
                return False
            time.sleep(0.05)
        if process.returncode:
            raise RuntimeError("Windows speech synthesis failed.")
        return True
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()
