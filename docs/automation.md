# Milestone 6 — Computer automation

The Tools page runs explicit user-selected operations through a closed tool
registry and executor. No model output is executed. No extra packages are needed.

## Tools

- Approve a specific local folder for the current app session. Revoke it when
  finished. Permission resets on restart. An entire drive cannot be approved.
- Read UTF-8 `.txt`, `.md`, `.csv`, or `.log` files up to 1 MiB. Previews stay in
  the Tools page and never enter chat context.
- Search filenames within that folder. Search stops at 100 matches or 5,000
  visited entries. Symlinks and junctions are excluded.
- Copy a file up to 10 MiB to a new relative path within the approved folder.
  Every copy needs confirmation. Existing files are never overwritten. Partial
  copies are removed if cancellation or an error occurs.
- Open Notepad or Calculator after confirmation. The executor launches only
  fixed Windows System32 executable paths, without a shell or extra arguments.

Use relative paths such as `notes.txt` and `archive/notes-copy.txt`. Destination
directories must exist. Links, junctions, path traversal and alternate data
streams are rejected. Use folders you control; path checks are not an OS sandbox
against another process concurrently replacing filesystem entries.

Emergency Stop prevents new tools and cooperatively cancels running file work.
It cannot reverse completed work or close apps already launched. Resume tools
explicitly after stopping. A pending operating-system I/O call must return before
cancellation can finish. Closing the dashboard during a tool operation requests
cancellation and requires closing again when the operation has finished.

Execution audit records are in `%LOCALAPPDATA%\SkyWalker\logs\tools.jsonl`
(or the configured data directory). Records contain UTC time, tool name and
status; no file paths, file contents, prompts, passwords or tokens are logged.

This milestone provides manual tool execution. AI tool calling, destructive file
operations, arbitrary shell commands, installation and administrative operations
are not enabled.

## System monitor

The System Monitor page samples CPU, RAM, disk free space and battery status every
three seconds. Dashboard CPU/RAM/battery use the same readings. CPU requires two
samples; unavailable counters display an unavailable state. The disk measurement
is for the application data drive. Ollama status remains the existing startup
check, not a live health check.

Windows counters use the built-in Kernel32 APIs through Python ctypes and run in
the installed native ARM64 Python process. References:

- https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-getsystemtimes
- https://learn.microsoft.com/en-us/windows/win32/api/sysinfoapi/nf-sysinfoapi-globalmemorystatusex
- https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-getsystempowerstatus

## Voice status

Wake-word detection is deferred and its dashboard control is disabled. Manual
microphone input and speech output remain available. Milestone 5 retains this
open item; passing tool tests does not verify wake detection.
