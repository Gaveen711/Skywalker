# Voice interaction — Milestone 5

**Current status:** Hey Sky detection is deferred because it is not reliable on
the target machine. Its dashboard checkbox is disabled. The experimental
implementation described below is retained for future work; use Record voice.

Install microphone support in the project virtual environment:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[voice]"
```

The dashboard's Record voice button captures a mono PCM WAV directly at 16 kHz.
Click Finish recording when done speaking, or capture ends after 15 seconds.
Capture runs in a background thread. Cancelled or failed captures are
deleted. A successful clip replaces the previous clip at
`%LOCALAPPDATA%\SkyWalker\audio\clip.wav` (or the configured data directory).

The sidebar's Assistant activity panel reports runtime, chat, and microphone
states independently. Recording is indicated after the input stream opens;
transcription explicitly shows that the microphone is off. A busy bar remains
visible while any operation is active. Runtime availability reflects the
startup check, not a continuously monitored connection. Errors remain visible
after their worker finishes.
Use Delete recording to remove it. Audio is not uploaded or added to AI context.

The device enumeration check detected the Qualcomm microphone array. Hardware
recording quality still needs a user initiated recording check in the dashboard.

While recording, delayed transcription previews appear in the chat input when
available. They may lag several seconds behind speech. After capture, the full
clip is transcribed and replaces the preview; review it and press Send. The ARM64 CPU runtime b5454 and
English small model are installed under `%LOCALAPPDATA%\SkyWalker\runtimes`
and `%LOCALAPPDATA%\SkyWalker\models`, outside Git. The runtime archive was
verified against its published SHA-256. A public JFK sample was successfully
transcribed on the target machine. Microphone transcription quality remains
to be checked by the user. The small.en model matched the SHA-1 published by
whisper.cpp and transcribed the public JFK sample in 5.5 seconds on this machine.
Older clips at other sample rates must be recorded again; no basic resampling
is applied. Devices that reject 16 kHz report an input configuration error.

Cancellation during transcription discards the result after the subprocess
finishes (up to a 180-second timeout).

## Speech output

Speak replies is enabled by default. Replies are spoken by the installed
Windows `System.Speech` voice using Windows PowerShell; no additional speech
engine download is needed. Text is passed to the child process as base64 data,
not inserted into the PowerShell script. Use Stop while speaking to terminate
playback. Voice availability depends on the Windows speech voices installed on
the machine. The app does not claim speech output is available until the
PowerShell synthesis process exits successfully.

## Hey Sky (experimental)

The optional Listen for Hey Sky control uses the local Whisper English model to
transcribe short microphone segments and look for the phrase. It is an
ASR-based phrase spotter, not a dedicated low-power wake-word detector; while
enabled it keeps the microphone open and can use noticeable CPU and may miss or
mishear the phrase. Disable it at any time by turning the control off. Saying
"Hey Sky" followed by a command puts that command in the input for review.
Saying only "Hey Sky" starts a normal voice recording so you can then
speak and review the transcript. No audio leaves the machine.

Whisper and its English model must be installed at the documented local paths
for voice input and this experimental phrase spotter. The Windows built-in
speech synthesis voice handles spoken output separately.
