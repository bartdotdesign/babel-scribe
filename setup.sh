#!/bin/bash
# BabelScribe — Setup Script
# Creates a virtual environment, installs dependencies, registers the MCP
# server with Claude Code, and installs the /dictate slash command.
#
# Usage: bash setup.sh
#
# Copyright (C) 2026 BabelScribe Contributors
# Licensed under GPLv3 — see LICENSE file for details.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# ── Colors ───────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BOLD='\033[1m'
NC='\033[0m' # No Color

info()  { echo -e "${BOLD}$1${NC}"; }
ok()    { echo -e "${GREEN}$1${NC}"; }
warn()  { echo -e "${YELLOW}$1${NC}"; }
error() { echo -e "${RED}$1${NC}" >&2; }

# ── Find Python 3.9+ ────────────────────────────────────────────────
find_python() {
    for cmd in python3.12 python3.11 python3.10 python3.9 python3; do
        if command -v "$cmd" &>/dev/null; then
            version=$("$cmd" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null)
            major=$(echo "$version" | cut -d. -f1)
            minor=$(echo "$version" | cut -d. -f2)
            if [ "$major" -ge 3 ] && [ "$minor" -ge 9 ]; then
                echo "$cmd"
                return 0
            fi
        fi
    done
    return 1
}

info "BabelScribe — Offline Voice Dictation for Claude Code"
echo ""

# ── Check Python ─────────────────────────────────────────────────────
info "Step 1/4: Checking Python..."
PYTHON=$(find_python) || {
    error "Python 3.9+ is required but not found."
    echo ""
    echo "Install Python via:"
    echo "  macOS:  brew install python3"
    echo "  Linux:  sudo apt install python3"
    echo ""
    exit 1
}
ok "  Found $PYTHON ($($PYTHON --version 2>&1))"

# ── Create virtual environment ───────────────────────────────────────
info "Step 2/4: Creating virtual environment..."
if [ -d "$SCRIPT_DIR/venv" ]; then
    warn "  venv/ already exists — reusing it"
else
    "$PYTHON" -m venv "$SCRIPT_DIR/venv"
    ok "  Created venv/"
fi

# ── Install dependencies ─────────────────────────────────────────────
info "Step 3/4: Installing dependencies (this may take a minute)..."
"$SCRIPT_DIR/venv/bin/pip" install --quiet --upgrade pip
"$SCRIPT_DIR/venv/bin/pip" install --quiet -r "$SCRIPT_DIR/requirements.txt"
ok "  Dependencies installed"

# ── Register with Claude Code ────────────────────────────────────────
info "Step 4/4: Registering with Claude Code..."

VENV_PYTHON="$SCRIPT_DIR/venv/bin/python3"
SERVER="$SCRIPT_DIR/server.py"

if command -v claude &>/dev/null; then
    # Remove existing registration if present (ignore errors)
    claude mcp remove babel-scribe 2>/dev/null || true

    # Register the MCP server
    claude mcp add --transport stdio babel-scribe -- "$VENV_PYTHON" "$SERVER"
    ok "  MCP server registered as 'babel-scribe'"
else
    warn "  Claude CLI not found — skipping auto-registration."
    echo ""
    echo "  Register manually by running:"
    echo "    claude mcp add --transport stdio babel-scribe -- $VENV_PYTHON $SERVER"
    echo ""
fi

# ── Install /dictate slash command ───────────────────────────────────
COMMANDS_DIR="$HOME/.claude/commands"
if [ -d "$HOME/.claude" ]; then
    mkdir -p "$COMMANDS_DIR"
    cp "$SCRIPT_DIR/commands/dictate.md" "$COMMANDS_DIR/dictate.md"
    ok "  Installed /dictate slash command"
else
    warn "  ~/.claude/ not found — skipping slash command install."
    echo "  You can copy it manually later:"
    echo "    mkdir -p ~/.claude/commands"
    echo "    cp $SCRIPT_DIR/commands/dictate.md ~/.claude/commands/"
fi

# ── Done ─────────────────────────────────────────────────────────────
echo ""
ok "Setup complete!"
echo ""
echo "  Usage:"
echo "    1. Open Claude Code in any project"
echo "    2. Type /dictate and press Enter"
echo "    3. Speak — recording stops automatically when you pause"
echo "    4. Your words appear in the conversation"
echo ""
echo "  You can also just say 'dictate' or 'record what I say' to Claude."
echo ""
echo "  Note: On first use, the Whisper model (~150MB) will be downloaded."
echo "        macOS will also ask for Microphone permission for your terminal."
echo ""
