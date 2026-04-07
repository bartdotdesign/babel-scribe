# BabelScribe — Instructions for Claude

This is the BabelScribe project, an offline voice dictation MCP server for Claude Code.

## If the user needs help installing

Walk them through these steps:

1. **Run the setup script:**
   ```bash
   bash setup.sh
   ```
   This creates a Python virtual environment, installs dependencies, registers the MCP server with Claude Code, and installs the `/dictate` slash command. It takes about a minute.

2. **Restart Claude Code** after setup completes (the MCP server registration takes effect on restart).

3. **Test it:** The user can type `/dictate` and speak. Their words will appear in the conversation.

## If the user has issues

### Setup failed — Python not found
They need Python 3.9 or newer. Suggest:
- macOS: `brew install python3`
- Linux: `sudo apt install python3`

### Setup failed — Claude CLI not found
They need Claude Code installed first. Point them to https://claude.ai/download.

### Microphone not working
On macOS, the terminal app needs Microphone permission. Guide them to: **System Settings > Privacy & Security > Microphone** and enable their terminal app.

### "No audio captured"
- Check their microphone is working in another app
- Make sure they're speaking within a few seconds of the tool being called
- The recording auto-stops after 2 seconds of silence

### First dictation is slow
Normal — the Whisper model (~150MB) downloads on first use. After that it's cached.

### Want to change the Whisper model
Edit `MODEL_SIZE` at the top of `server.py`. Options: `tiny`, `base` (default), `small`, `medium`, `large-v3`. Larger models are more accurate but slower.

## Project structure

- `server.py` — The MCP server. This is the main file.
- `setup.sh` — One-command installer.
- `requirements.txt` — Python dependencies.
- `commands/dictate.md` — The `/dictate` slash command source (copied to `~/.claude/commands/` during setup).

## How dictation works

1. Claude Code calls the `dictate` MCP tool
2. The microphone starts recording
3. Ambient noise is calibrated for 0.5 seconds
4. When the user stops speaking (2s silence), recording stops
5. Audio is transcribed locally using Whisper (faster-whisper, int8 CPU)
6. Transcribed text is returned to the conversation
