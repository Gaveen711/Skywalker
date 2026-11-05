"""Closed registry: no dynamic shell commands or model-supplied code."""
from dataclasses import dataclass


@dataclass(frozen=True)
class ToolDefinition:
    label: str
    confirmation: bool = False


TOOLS = {
    "read": ToolDefinition("Read text file"),
    "search": ToolDefinition("Search filenames"),
    "copy": ToolDefinition("Copy file", confirmation=True),
    "launch": ToolDefinition("Open application", confirmation=True),
}
