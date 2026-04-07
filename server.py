#!/usr/bin/env python3
"""
BabelScribe — Offline voice dictation for Claude Code via MCP.

Records from the microphone, detects silence to auto-stop, and transcribes
locally using Whisper. No audio leaves your machine.

Copyright (C) 2026 BabelScribe Contributors
This program is free software: you can redistribute it and/or modify it
under the terms of the GNU General Public License v3.0.
See LICENSE file for details.
"""

import sys
import os
import tempfile
import time
import wave

import numpy as np
import sounddevice as sd

# Suppress CTranslate2 and Whisper logging before import
os.environ["CT2_VERBOSE"] = "0"
import logging
logging.disable(logging.CRITICAL)

from faster_whisper import WhisperModel
from mcp.server.fastmcp import FastMCP

# ── Configuration ────────────────────────────────────────────────────
SAMPLE_RATE = 16000
CHANNELS = 1
MODEL_SIZE = "base"
DEVICE = "cpu"
COMPUTE_TYPE = "int8"

SILENCE_THRESHOLD_MULTIPLIER = 3  # threshold = ambient_rms * this
MIN_SILENCE_THRESHOLD = 300       # absolute minimum RMS threshold
SILENCE_DURATION = 2.0            # seconds of silence after speech to stop
CALIBRATION_DURATION = 0.5        # seconds to measure ambient noise
MIN_RECORDING_DURATION = 1.0      # don't stop before this
MAX_RECORDING_DURATION = None     # no time limit (set to e.g. 60.0 for a cap)

# ── Globals ──────────────────────────────────────────────────────────
_model = None

mcp = FastMCP("babel-scribe")


def get_model():
    global _model
    if _model is None:
        _model = WhisperModel(MODEL_SIZE, device=DEVICE, compute_type=COMPUTE_TYPE)
    return _model


def save_wav(audio, path):
    with wave.open(path, "wb") as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(audio.tobytes())


def compute_rms(audio_chunk):
    return np.sqrt(np.mean(audio_chunk.astype(np.float64) ** 2))


def record_with_silence_detection():
    """Record audio, auto-stop on silence after speech."""
    import threading

    frames = []
    stop_event = threading.Event()
    speech_detected = False
    silence_start = None
    threshold = MIN_SILENCE_THRESHOLD
    recording_start = None
    calibration_frames = []

    def callback(indata, frame_count, time_info, status):
        nonlocal speech_detected, silence_start, threshold, recording_start, calibration_frames

        frames.append(indata.copy())
        elapsed = time.time() - recording_start if recording_start else 0
        rms = compute_rms(indata)

        # Calibration phase: measure ambient noise
        if elapsed < CALIBRATION_DURATION:
            calibration_frames.append(rms)
            return

        # Set threshold after calibration
        if calibration_frames:
            ambient_rms = np.mean(calibration_frames)
            threshold = max(ambient_rms * SILENCE_THRESHOLD_MULTIPLIER, MIN_SILENCE_THRESHOLD)
            calibration_frames = []  # done calibrating

        # Don't stop before minimum duration
        if elapsed < MIN_RECORDING_DURATION:
            return

        # Max duration safety cap (if set)
        if MAX_RECORDING_DURATION and elapsed >= MAX_RECORDING_DURATION:
            stop_event.set()
            return

        # Silence detection
        if rms > threshold:
            speech_detected = True
            silence_start = None
        elif speech_detected:
            if silence_start is None:
                silence_start = time.time()
            elif time.time() - silence_start >= SILENCE_DURATION:
                stop_event.set()

    stream = sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype="int16",
        callback=callback,
    )

    recording_start = time.time()
    stream.start()
    stop_event.wait(timeout=MAX_RECORDING_DURATION)
    stream.stop()
    stream.close()

    if not frames:
        return None

    return np.concatenate(frames, axis=0)


def transcribe_audio(audio):
    model = get_model()
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=True) as tmp:
        save_wav(audio, tmp.name)
        segments, _ = model.transcribe(tmp.name, beam_size=5)
        text = " ".join(seg.text.strip() for seg in segments)
    return text


@mcp.tool()
def dictate() -> str:
    """
    Record voice from the microphone and transcribe it locally using Whisper.
    Recording auto-stops when you stop speaking (2 seconds of silence).
    All processing is 100% offline — no audio leaves the machine.
    """
    audio = record_with_silence_detection()

    if audio is None or len(audio) == 0:
        return "(no audio captured)"

    duration = len(audio) / SAMPLE_RATE
    text = transcribe_audio(audio)

    if not text.strip():
        return "(no speech detected)"

    return text.strip()


if __name__ == "__main__":
    mcp.run(transport="stdio")
