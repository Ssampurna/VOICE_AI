# app/asr.py
# -----------------------------------------------------------
# Automatic Speech Recognition module.
# Primary:  faster-whisper (efficient local transcription)
# Fallback: openai-whisper  (if faster-whisper unavailable)
# -----------------------------------------------------------

import os
import sys
import tempfile
from pathlib import Path

import certifi
os.environ["SSL_CERT_FILE"] = certifi.where()

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config.settings import (
    WHISPER_MODEL_SIZE,
    WHISPER_DEVICE,
    WHISPER_COMPUTE,
    WHISPER_LANGUAGE,
)
from app.utils import setup_logger

logger = setup_logger()

# Module-level model cache — loaded once, reused across calls
_whisper_model = None
_model_backend  = None   # "faster-whisper" or "openai-whisper"


def _load_model():
    """
    Load and cache the Whisper model.
    Tries faster-whisper first; falls back to openai-whisper.
    """
    global _whisper_model, _model_backend

    if _whisper_model is not None:
        return _whisper_model, _model_backend

    # ── Attempt faster-whisper ────────────────────────────────
    try:
        from faster_whisper import WhisperModel
        logger.info(f"⏳ Loading faster-whisper model '{WHISPER_MODEL_SIZE}'...")
        _whisper_model = WhisperModel(
            WHISPER_MODEL_SIZE,
            device=WHISPER_DEVICE,
            compute_type=WHISPER_COMPUTE,
        )
        _model_backend = "faster-whisper"
        logger.info("✅ faster-whisper model loaded.")
        return _whisper_model, _model_backend

    except ImportError:
        logger.warning("faster-whisper not found. Trying openai-whisper...")

    # ── Fallback: openai-whisper ──────────────────────────────
    try:
        import whisper
        logger.info(f"⏳ Loading openai-whisper model '{WHISPER_MODEL_SIZE}'...")
        _whisper_model = whisper.load_model(WHISPER_MODEL_SIZE)
        _model_backend = "openai-whisper"
        logger.info("✅ openai-whisper model loaded.")
        return _whisper_model, _model_backend

    except ImportError:
        raise RuntimeError(
            "No Whisper backend found. Install one:\n"
            "  pip install faster-whisper\n"
            "  OR: pip install openai-whisper"
        )


def _array_to_wav(audio_array: np.ndarray, sample_rate: int) -> str:
    """
    Write a numpy float32 audio array to a temporary WAV file.
    Returns the path string of the temp file.
    """
    try:
        from scipy.io import wavfile
    except ImportError:
        raise RuntimeError("scipy is required: pip install scipy")

    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    audio_int16 = (np.clip(audio_array, -1.0, 1.0) * 32767).astype(np.int16)
    wavfile.write(tmp.name, sample_rate, audio_int16)
    return tmp.name


def transcribe(
    audio_input,
    sample_rate: int = 16000,
) -> str:
    """
    Transcribe speech from audio.

    Args:
        audio_input: Either:
            - np.ndarray (float32 audio samples), OR
            - str / Path pointing to a .wav or .mp3 file
        sample_rate: Sample rate (used only if audio_input is ndarray).

    Returns:
        Transcribed text string (stripped).

    Raises:
        RuntimeError: If no Whisper backend is available.
        ValueError:   If the input type is unrecognized.
    """
    model, backend = _load_model()

    # Resolve input to a file path
    temp_path = None
    if isinstance(audio_input, np.ndarray):
        temp_path = _array_to_wav(audio_input, sample_rate)
        audio_path = temp_path
    elif isinstance(audio_input, (str, Path)):
        audio_path = str(audio_input)
    else:
        raise ValueError(f"Unsupported audio_input type: {type(audio_input)}")

    logger.info(f"🧠 Transcribing with {backend}...")

    try:
        if backend == "faster-whisper":
            segments, info = model.transcribe(
                audio_path,
                language=WHISPER_LANGUAGE,
                beam_size=5,
                vad_filter=True,       # Skip silence — faster & cleaner
                vad_parameters=dict(min_silence_duration_ms=500),
            )
            text = " ".join(seg.text.strip() for seg in segments)
            logger.info(f"   Detected language: {info.language} "
                        f"(confidence: {info.language_probability:.0%})")

        else:  # openai-whisper
            import whisper
            result = model.transcribe(
                audio_path,
                language=WHISPER_LANGUAGE,
                fp16=False,
            )
            text = result["text"]

        text = text.strip()
        if not text:
            logger.warning("⚠️ Transcription returned empty text.")
            return "(no speech detected)"

        logger.info(f"✅ Transcript: \"{text[:80]}{'...' if len(text) > 80 else ''}\"")
        return text

    except Exception as e:
        raise RuntimeError(f"Transcription failed: {e}") from e

    finally:
        # Clean up temp WAV file if we created one
        if temp_path and Path(temp_path).exists():
            try:
                Path(temp_path).unlink()
            except OSError:
                pass