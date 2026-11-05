import json
import tempfile
import unittest
from pathlib import Path
from threading import Event
from unittest.mock import patch

from skywalker.tools.executor import ToolExecutor
from skywalker.tools.file_tools import FileTools


class ToolTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.files = FileTools(self.root)
        self.executor = ToolExecutor(self.root / "audit.jsonl")
        (self.root / "sample.txt").write_text("private content", encoding="utf-8")

    def test_paths_cannot_escape_or_access_streams(self):
        for path in ("../secret.txt", str(self.root / "sample.txt"), "sample.txt:stream"):
            with self.assertRaises((ValueError, PermissionError)):
                self.files.checked(path)

    def test_read_requires_permission_and_does_not_log_contents(self):
        with self.assertRaises(PermissionError):
            self.executor.execute("read", None, "sample.txt")
        self.assertEqual(self.executor.execute("read", self.root, "sample.txt"), "private content")
        log = self.executor.audit.read_text()
        self.assertNotIn("private content", log)
        self.assertNotIn("sample.txt", log)
        self.assertEqual(json.loads(log.splitlines()[-1])["status"], "completed")

    def test_copy_requires_confirmation_and_never_overwrites(self):
        with self.assertRaises(PermissionError):
            self.executor.execute("copy", self.root, "sample.txt", "copy.txt")
        self.executor.execute("copy", self.root, "sample.txt", "copy.txt", confirmed=True)
        self.assertEqual((self.root / "copy.txt").read_text(), "private content")
        with self.assertRaises(FileExistsError):
            self.executor.execute("copy", self.root, "sample.txt", "copy.txt", confirmed=True)
        self.assertEqual((self.root / "copy.txt").read_text(), "private content")

    def test_emergency_stop_blocks_launch_and_file_operations(self):
        self.executor.cancel.set()
        with patch("skywalker.tools.executor.subprocess.Popen") as launch:
            with self.assertRaises(InterruptedError):
                self.executor.execute("launch", None, "Notepad", confirmed=True)
            launch.assert_not_called()
        with self.assertRaises(InterruptedError):
            self.executor.execute("read", self.root, "sample.txt")

    def test_cancelled_copy_removes_partial_destination(self):
        cancel = Event()
        cancel.set()
        with self.assertRaises(InterruptedError):
            self.files.copy("sample.txt", "partial.txt", cancel)
        self.assertFalse((self.root / "partial.txt").exists())

    def test_arbitrary_commands_and_apps_are_rejected(self):
        with self.assertRaises(ValueError):
            self.executor.execute("shell", None, "echo anything")
        with self.assertRaises(PermissionError):
            self.executor.execute("launch", None, "powershell.exe", confirmed=True)

    def test_search_is_case_insensitive_and_bounded_to_folder(self):
        self.assertEqual(self.files.search("SAMPLE", Event()), "sample.txt")
