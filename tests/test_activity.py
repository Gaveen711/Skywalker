"""Activity states must reflect independent operations and preserve failures."""

import os
import tempfile
import unittest
from threading import Event
from types import SimpleNamespace
from unittest.mock import patch

from PySide6.QtWidgets import QApplication

from skywalker.presentation.activity import ActivityPanel
from skywalker.presentation.window import MainWindow


class ActivityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_busy_until_every_operation_finishes(self):
        panel = ActivityPanel()
        panel.set_state("Chat", "Writing reply", busy=True)
        panel.set_state("Microphone", "Recording", busy=True)
        panel.set_state("Chat", "Complete")
        self.assertEqual(panel.progress.maximum(), 0)
        panel.set_state("Microphone", "Done")
        self.assertEqual(panel.progress.maximum(), 1)
        self.assertTrue(panel.progress.isHidden())

    def test_error_and_cancellation_survive_worker_completion(self):
        with tempfile.TemporaryDirectory() as folder, patch.dict(
            os.environ, {"SKYWALKER_DATA_DIR": folder}
        ), patch.object(MainWindow, "discover_models"):
            window = MainWindow()
            worker = SimpleNamespace(cancel=Event(), response="", isRunning=lambda: False)
            window.chat_worker = worker
            window.chat_failed("Test failure")
            window.chat_finished()
            self.assertEqual(window.activity.states["Chat"], "Reply failed")
            window.microphone_worker = worker
            window.recording_started()
            self.assertTrue(window.activity.busy["Microphone"])
            window.transcription_started("unused")
            self.assertIn("mic off", window.activity.states["Microphone"])
            window.voice_failed("Test failure")
            window.voice_finished()
            self.assertEqual(window.activity.states["Microphone"], "Voice input failed")
            worker.cancel.set()
            window.voice_finished()
            self.assertFalse(window.activity.busy["Microphone"])
            self.assertIn("Cancelled", window.activity.states["Microphone"])
            window.close()
