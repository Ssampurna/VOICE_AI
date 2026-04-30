# config/settings.py
# -----------------------------------------------------------
# Centralized configuration for the Voice AI Field Notes App.
# All paths, model names, and tunable parameters live here.
# -----------------------------------------------------------

import os
from pathlib import Path

# ── Project root (two levels up from this file) ──────────────
BASE_DIR = Path(__file__).resolve().parent.parent

# ── Directory paths ──────────────────────────────────────────
DATA_DIR            = BASE_DIR / "data" / "sample_audio"
TRANSCRIPTS_DIR     = BASE_DIR / "outputs" / "transcripts"
AUDIO_OUT_DIR       = BASE_DIR / "outputs" / "audio"

# Auto-create output directories if they don't exist
TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
AUDIO_OUT_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

# ── ASR settings (faster-whisper / whisper) ──────────────────
WHISPER_MODEL_SIZE  = "base"          # tiny | base | small | medium | large
WHISPER_DEVICE      = "cpu"           # cpu | cuda
WHISPER_COMPUTE     = "int8"          # int8 | float16 | float32
WHISPER_LANGUAGE    = "en"            # None = auto-detect

# ── Audio recording settings ─────────────────────────────────
RECORD_SAMPLE_RATE  = 16000          # Hz — Whisper works best at 16 kHz
RECORD_CHANNELS     = 1              # Mono
RECORD_DURATION     = 10             # Default max seconds to record
RECORD_CHUNK_SIZE   = 1024

# ── LLM settings ─────────────────────────────────────────────
GROQ_MODEL          = "llama-3.1-8b-instant"   
LLM_MAX_TOKENS      = 512
LLM_TEMPERATURE     = 0.7

# System prompt that shapes the assistant's persona
SYSTEM_PROMPT = (
    "You are a Field Notes AI Assistant helping scientists, researchers, "
    "and journalists capture and enrich their observations. "
    "When the user shares a field observation, you:\n"
    "1. Briefly acknowledge the observation\n"
    "2. Suggest one or two relevant follow-up questions or considerations\n"
    "3. Offer a concise structured summary tagged as [SUMMARY]\n"
    "Keep responses clear, professional, and under 150 words."
)

# ── TTS settings ─────────────────────────────────────────────
TTS_LANGUAGE        = "en"
TTS_SLOW            = False

# ── Logging ──────────────────────────────────────────────────
LOG_LEVEL           = "INFO"          # DEBUG | INFO | WARNING | ERROR