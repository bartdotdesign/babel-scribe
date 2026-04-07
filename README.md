# BabelScribe

**Offline voice dictation for Claude Code.** Speak, and your words appear directly in the conversation. No audio leaves your machine.

> *"The Babel Fish is small, yellow, and simultaneously translates any language in the universe."*
> *— The Hitchhiker's Guide to the Galaxy*
>
> Like the Babel Fish that translates any spoken language, **BabelScribe** translates your voice into text — right inside Claude Code. Powered by OpenAI's Whisper model, running 100% locally on your machine.

## Quick Start

```bash
git clone https://github.com/bartdotdesign/babel-scribe.git
cd babel-scribe
bash setup.sh
```

That's it. The setup script handles everything:
- Creates a Python virtual environment
- Installs dependencies
- Registers the MCP server with Claude Code
- Installs the `/dictate` slash command

## Usage

Once installed, open Claude Code in any project and:

**Option 1 — Slash command:**
```
/dictate
```

**Option 2 — Natural language:**
Just tell Claude to "dictate", "record what I say", or "take voice input".

**What happens:**
1. Your microphone starts recording
2. Ambient noise is auto-calibrated (first 0.5 seconds)
3. When you stop speaking (2 seconds of silence), recording stops automatically
4. Your speech is transcribed and appears in the conversation

## How It Works

BabelScribe is an [MCP (Model Context Protocol)](https://modelcontextprotocol.io/) server that exposes a `dictate` tool to Claude Code. When called:

1. Records audio from your default microphone using `sounddevice`
2. Detects when you've stopped speaking via RMS-based silence detection
3. Transcribes the audio locally using [faster-whisper](https://github.com/SYSTRAN/faster-whisper) (a CTranslate2-based Whisper implementation)
4. Returns the transcribed text to Claude

Everything runs on your machine. No audio is sent to any cloud service.

## Configuration

You can tune these settings at the top of `server.py`:

| Setting | Default | Description |
|---|---|---|
| `MODEL_SIZE` | `"base"` | Whisper model size: `tiny`, `base`, `small`, `medium`, `large-v3` |
| `SILENCE_DURATION` | `2.0` | Seconds of silence before auto-stop |
| `MIN_RECORDING_DURATION` | `1.0` | Minimum recording time before silence detection activates |
| `MAX_RECORDING_DURATION` | `None` | Maximum recording length (set to e.g. `60.0` for a cap) |
| `SILENCE_THRESHOLD_MULTIPLIER` | `3` | How much louder than ambient noise counts as speech |

**Model sizes** (trade-off: accuracy vs speed/RAM):

| Model | Size | RAM | Speed | Accuracy |
|---|---|---|---|---|
| `tiny` | ~75MB | ~1GB | Fastest | Basic |
| `base` | ~150MB | ~1GB | Fast | Good (default) |
| `small` | ~500MB | ~2GB | Medium | Better |
| `medium` | ~1.5GB | ~5GB | Slower | Great |
| `large-v3` | ~3GB | ~10GB | Slowest | Best |

## Troubleshooting

### "Microphone permission denied"
On macOS, your terminal app needs Microphone access. Go to **System Settings > Privacy & Security > Microphone** and enable your terminal (Terminal, iTerm2, etc.).

### "No audio captured" or "No speech detected"
- Check that your microphone is working (test in another app)
- Speak clearly and within a few seconds of the recording starting
- Try increasing `SILENCE_DURATION` if it cuts off too early

### "Python 3.9+ required"
Install a recent Python version:
```bash
# macOS
brew install python3

# Ubuntu/Debian
sudo apt install python3
```

### First use is slow
The first time you dictate, the Whisper model (~150MB for `base`) is downloaded and cached. Subsequent uses are fast.

### "Claude CLI not found" during setup
Install Claude Code first: https://claude.ai/download — then re-run `bash setup.sh`.

## Requirements

- **macOS** or **Linux** (macOS tested, Linux should work)
- **Python 3.9+**
- **Working microphone**
- **Claude Code** (CLI, desktop app, or IDE extension)

## License

BabelScribe is licensed under the [GNU General Public License v3.0](LICENSE).

You are free to use, modify, and distribute this software, provided that any derivative works are also released under the GPLv3.
