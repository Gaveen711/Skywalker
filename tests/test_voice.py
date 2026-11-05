import unittest
from threading import Event
from unittest.mock import MagicMock, patch

from skywalker.infrastructure.speech import speak
from skywalker.presentation.wake_worker import extract_wake_command


class WakePhraseTests(unittest.TestCase):
    def test_extracts_command_after_punctuation_and_case(self):
        self.assertEqual(extract_wake_command("Hey, SKY! Open settings."), "open settings")

    def test_phrase_without_command_returns_empty_command(self):
        self.assertEqual(extract_wake_command("Hey Sky"), "")

    def test_unmatched_phrase_returns_none(self):
        self.assertIsNone(extract_wake_command("Hi there, Sky"))


class SpeechTests(unittest.TestCase):
    @patch("skywalker.infrastructure.speech.shutil.which", return_value="powershell.exe")
    @patch("skywalker.infrastructure.speech.subprocess.Popen")
    def test_speaks_text_in_child_process(self, popen, _which):
        process = MagicMock()
        process.poll.return_value = 0
        process.returncode = 0
        popen.return_value = process

        self.assertTrue(speak("hello", Event()))

        args, options = popen.call_args
        self.assertEqual(args[0][0], "powershell.exe")
        self.assertIn("SKYWALKER_TTS_TEXT", options["env"])

    @patch("skywalker.infrastructure.speech.shutil.which", return_value="powershell.exe")
    @patch("skywalker.infrastructure.speech.subprocess.Popen")
    def test_interrupt_terminates_speech_process(self, popen, _which):
        process = MagicMock()
        process.poll.side_effect = [None, 0]
        popen.return_value = process
        cancel = Event()

        def cancel_on_start():
            cancel.set()

        self.assertFalse(speak("hello", cancel, cancel_on_start))
        process.terminate.assert_called_once()


if __name__ == "__main__":
    unittest.main()
