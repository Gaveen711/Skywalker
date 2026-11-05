import tempfile
import unittest
import wave
from pathlib import Path
from threading import Event
from unittest.mock import MagicMock, patch

from skywalker.infrastructure.microphone import record_clip


class MicrophoneTests(unittest.TestCase):
    def test_capture_writes_valid_pcm_wav(self):
        stream = MagicMock()
        stream.__enter__.return_value = stream
        stream.read.side_effect = lambda count: (bytes(count * 2), False)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "clip.wav"
            with patch("sounddevice.check_input_settings"), patch(
                "sounddevice.RawInputStream", return_value=stream
            ):
                record_clip(path, Event(), seconds=1)
            with wave.open(str(path), "rb") as audio:
                self.assertEqual(audio.getnframes(), 16000)
                self.assertEqual(audio.getframerate(), 16000)
                self.assertEqual(audio.getsampwidth(), 2)
                self.assertEqual(audio.getnchannels(), 1)
