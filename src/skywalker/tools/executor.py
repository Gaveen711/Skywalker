"""Permission checks, cancellation and privacy-preserving execution audit."""
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from threading import Event

from skywalker.tools.file_tools import FileTools
from skywalker.tools.registry import TOOLS

APPLICATIONS = {"Notepad": "notepad.exe", "Calculator": "calc.exe"}


class ToolExecutor:
    def __init__(self, audit: Path) -> None:
        self.audit = audit
        self.cancel = Event()

    def log(self, tool: str, status: str) -> None:
        self.audit.parent.mkdir(parents=True, exist_ok=True)
        with self.audit.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps({"time": datetime.now(timezone.utc).isoformat(),
                                     "tool": tool if tool in TOOLS else "unknown", "status": status}) + "\n")

    def execute(self, tool: str, root: Path | None, source: str, destination: str = "",
                *, confirmed: bool = False) -> str:
        self.log(tool, "requested")
        try:
            if self.cancel.is_set():
                raise InterruptedError("Emergency stop is active. Resume tools first.")
            definition = TOOLS.get(tool)
            if definition is None:
                raise ValueError("Unknown tool")
            if definition.confirmation and not confirmed:
                raise PermissionError("This operation requires confirmation.")
            if tool == "launch":
                if os.name != "nt" or source not in APPLICATIONS:
                    raise PermissionError("Application is not approved.")
                executable = Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32" / APPLICATIONS[source]
                if not executable.is_file():
                    raise FileNotFoundError("Approved application is unavailable.")
                if self.cancel.is_set():
                    raise InterruptedError("Stopped")
                subprocess.Popen([str(executable)], shell=False, cwd=executable.parent)
                result = f"Opened {source}."
            else:
                if root is None:
                    raise PermissionError("Approve a folder first.")
                files = FileTools(root)
                result = files.copy(source, destination, self.cancel) if tool == "copy" else getattr(files, tool)(source, self.cancel)
            self.log(tool, "completed")
            return result
        except Exception:
            self.log(tool, "stopped" if self.cancel.is_set() else "failed")
            raise
