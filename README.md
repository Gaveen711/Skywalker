# Sky Walker

Sky Walker is an offline-first personal desktop assistant. The repository
contains the foundation, Qt desktop shell, local Ollama chat integration, and
local voice input/output, controlled desktop tools, and system monitoring.

## Requirements

- Python 3.12 or newer. The current development machine uses Python 3.13.9 on
  Windows 11 ARM64.
- PySide6 Essentials 6.12 (a native Windows ARM64 wheel is published).
- Git.

The desktop app uses PySide6 Essentials and talks to the local Ollama HTTP API
with Python's standard library. Package installation uses the setuptools build
backend declared in `pyproject.toml`.

## Set up a development environment

From the repository root in PowerShell:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .
```

If the Python launcher does not detect an installation, create the environment
with the full path to `python.exe` instead. `python -m pip install -e .` may
need network access to install the build backend; application runtime use does
not require internet access.

## Run

From the project folder in PowerShell, run `.\run`.

The launcher opens the dashboard using the project's virtual environment.

Startup configures local rotating logs, checks Ollama, and opens the desktop
window. Application data is stored under `%LOCALAPPDATA%\SkyWalker` by
default. Set `SKYWALKER_DATA_DIR` to use a different local directory.

The default model is `qwen3.5:4b`. Override it with `SKYWALKER_MODEL`; set
`SKYWALKER_OLLAMA_URL` or `SKYWALKER_SYSTEM_PROMPT` to change the local runtime
URL or assistant instruction. Example values are in `.env.example`; copy them
to your PowerShell environment or a local `.env` file (the app does not load
`.env` automatically).

## Verify

```powershell
python -m unittest discover -s tests -v
```

## Project structure

```text
src/skywalker/       Application package
  core/              Configuration and logging
tests/               Standard-library unit tests
docs/                Architecture and development notes
```

The dashboard reports Ollama connectivity and installed models. Chat replies
stream in the window and use the current in-memory conversation as context.
Conversations are saved locally to SQLite. Use Conversations to start a new
chat, reopen a saved chat, or delete one after confirmation. Data is stored in
the configured application data directory, outside the repository by default.
SQLite is provided by Python itself, with no additional platform dependency.
The database is not encrypted; Windows account permissions protect its files.

Voice setup and the experimental "Hey Sky" listener are documented in
[`docs/voice.md`](docs/voice.md). Microphone input requires the optional
`voice` extra and the separately installed local Whisper runtime/model. Spoken
output uses the built-in Windows speech voice.

Milestone 6 adds the Tools and System Monitor pages. Approve a folder for the
current session to preview, search and copy files, or launch an approved app
after confirmation. See [`docs/automation.md`](docs/automation.md) for limits,
audit logging and emergency stop behavior. Hey Sky is deferred and disabled;
manual voice recording is available.
