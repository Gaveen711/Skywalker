"""Bounded operations in an explicitly selected directory."""
import os
from pathlib import Path
from threading import Event


class FileTools:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve(strict=True)
        if root.absolute() != self.root:
            raise PermissionError("Approved folder must not pass through a link or junction.")
        if not self.root.is_dir() or self.root == Path(self.root.anchor):
            raise ValueError("Choose a specific folder, not an entire drive.")

    def checked(self, value: str, *, destination: bool = False) -> Path:
        candidate = Path(value)
        if not value or candidate.is_absolute() or candidate.drive or ".." in candidate.parts:
            raise ValueError("Use a relative path inside the approved folder.")
        if any(":" in part for part in candidate.parts):
            raise ValueError("Alternate data streams are not allowed.")
        path = self.root
        for part in candidate.parts:
            path = path / part
            if path.is_symlink() or path.is_junction():
                raise PermissionError("Links and junctions are not allowed.")
        resolved = path.resolve(strict=not destination)
        if not resolved.is_relative_to(self.root):
            raise PermissionError("Path is outside the approved folder.")
        if destination and not resolved.parent.is_dir():
            raise ValueError("Destination folder must already exist.")
        return resolved

    def read(self, name: str, cancel: Event) -> str:
        path = self.checked(name)
        if path.suffix.lower() not in {".txt", ".md", ".csv", ".log"}:
            raise ValueError("Preview supports .txt, .md, .csv and .log files.")
        with path.open("rb") as stream:
            content = stream.read(1_048_577)
        if len(content) > 1_048_576:
            raise ValueError("Preview limit is 1 MiB.")
        if cancel.is_set():
            raise InterruptedError("Stopped")
        return content.decode("utf-8")

    def search(self, query: str, cancel: Event) -> str:
        if not query.strip():
            raise ValueError("Enter part of a filename.")
        results = []
        visited = 0
        def fail(error):
            raise error
        for directory, folders, files in os.walk(self.root, followlinks=False, onerror=fail):
            folders[:] = [name for name in folders if not (Path(directory) / name).is_symlink()
                          and not (Path(directory) / name).is_junction()]
            for name in folders + files:
                if cancel.is_set():
                    raise InterruptedError("Stopped")
                visited += 1
                path = Path(directory) / name
                if query.casefold() in name.casefold() and not path.is_symlink() and not path.is_junction():
                    results.append(str(path.relative_to(self.root)))
                if visited >= 5000 or len(results) >= 100:
                    return "\n".join(results) + "\nSearch limit reached; narrow the search."
        return "\n".join(results) or "No matches."

    def copy(self, source: str, destination: str, cancel: Event) -> str:
        source_path = self.checked(source)
        target = self.checked(destination, destination=True)
        if not source_path.is_file() or source_path.stat().st_size > 10 * 1024 * 1024:
            raise ValueError("Choose a file no larger than 10 MiB.")
        created = False
        try:
            with source_path.open("rb") as reader, target.open("xb") as writer:
                created = True
                total = 0
                while chunk := reader.read(65536):
                    if cancel.is_set():
                        raise InterruptedError("Stopped")
                    total += len(chunk)
                    if total > 10 * 1024 * 1024:
                        raise ValueError("Copy limit exceeded.")
                    writer.write(chunk)
            return "File copied."
        except Exception:
            if created:
                target.unlink(missing_ok=True)
            raise
