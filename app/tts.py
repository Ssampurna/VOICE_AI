# app/tts.py
# -----------------------------------------------------------
# Text-to-Speech module.
# Primary:  gTTS  (Google TTS — requires internet)
# Fallback: pyttsx3 (fully offline)
# -----------------------------------------------------------

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config.settings import (
    AUDIO_OUT_DIR,
    TTS_LANGUAGE,
    TTS_SLOW,
)
from app.utils import setup_logger, get_timestamp

logger = setup_logger()


def _tts_gtts(text: str, output_path: Path) -> Path:
    """
    Convert text to speech using gTTS and save as MP3.

    Args:
        text:        Text to convert.
        output_path: Destination .mp3 file path.

    Returns:
        Path to the saved .mp3 file.
    """
    try:
        from gtts import gTTS
    except ImportError:
        raise RuntimeError("gTTS not installed: pip install gtts")

    logger.info("🔊 Synthesizing speech with gTTS...")
    tts = gTTS(text=text, lang=TTS_LANGUAGE, slow=TTS_SLOW)
    tts.save(str(output_path))
    logger.info(f"✅ TTS audio saved: {output_path}")
    return output_path


def _tts_pyttsx3(text: str, output_path: Path) -> Path:
    """
    Convert text to speech using pyttsx3 (offline) and save as WAV.

    Args:
        text:        Text to convert.
        output_path: Destination .wav file path (extension adjusted automatically).

    Returns:
        Path to the saved audio file.
    """
    try:
        import pyttsx3
    except ImportError:
        raise RuntimeError("pyttsx3 not installed: pip install pyttsx3")

    # pyttsx3 saves as .wav; adjust extension
    wav_path = output_path.with_suffix(".wav")

    logger.info("🔊 Synthesizing speech with pyttsx3 (offline)...")
    engine = pyttsx3.init()

    # Configure voice properties
    engine.setProperty("rate", 165)    # words per minute
    engine.setProperty("volume", 0.9)  # 0.0 – 1.0

    # Prefer a female voice if available
    voices = engine.getProperty("voices")
    for voice in voices:
        if "female" in voice.name.lower() or "zira" in voice.name.lower():
            engine.setProperty("voice", voice.id)
            break

    engine.save_to_file(text, str(wav_path))
    engine.runAndWait()

    logger.info(f"✅ TTS audio saved: {wav_path}")
    return wav_path


def text_to_speech(text: str, timestamp: str = None) -> Path:
    """
    Convert text to speech, saving the output to the audio output directory.

    Tries gTTS first (better voice quality); falls back to pyttsx3 offline.

    Args:
        text:      The response text to synthesize.
        timestamp: Used in the output filename; auto-generated if None.

    Returns:
        Path to the generated audio file.

    Raises:
        RuntimeError: If both TTS backends fail.
    """
    if timestamp is None:
        timestamp = get_timestamp()

    if not text or not text.strip():
        raise ValueError("Cannot synthesize empty text.")

    # Truncate extremely long text to avoid TTS timeouts
    max_chars = 2000
    if len(text) > max_chars:
        logger.warning(f"⚠️ Response text truncated to {max_chars} chars for TTS.")
        text = text[:max_chars] + "..."

    mp3_path = AUDIO_OUT_DIR / f"response_{timestamp}.mp3"

    # ── Try gTTS ─────────────────────────────────────────────
    try:
        return _tts_gtts(text, mp3_path)
    except Exception as e:
        logger.warning(f"gTTS failed ({e}). Trying pyttsx3 fallback...")

    # ── Try pyttsx3 ──────────────────────────────────────────
    try:
        wav_path = AUDIO_OUT_DIR / f"response_{timestamp}.wav"
        return _tts_pyttsx3(text, wav_path)
    except Exception as e:
        raise RuntimeError(
            f"Both TTS backends failed.\n"
            f"  gTTS error:    check internet connection\n"
            f"  pyttsx3 error: {e}\n"
            f"Install with: pip install gtts pyttsx3"
        ) from e