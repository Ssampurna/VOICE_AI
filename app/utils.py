# app/utils.py
# -----------------------------------------------------------
# Utility helpers: logging setup, timestamping, file saving.
# -----------------------------------------------------------

import logging
import sys
from datetime import datetime
from pathlib import Path

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config.settings import TRANSCRIPTS_DIR, LOG_LEVEL


def setup_logger(name: str = "voice_ai") -> logging.Logger:
    """
    Create and return a configured logger with console output.
    """
    level = getattr(logging, LOG_LEVEL.upper(), logging.INFO)
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(message)s",
            datefmt="%H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


def get_timestamp() -> str:
    """Return a filesystem-safe timestamp string: YYYYMMDD_HHMMSS"""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def save_transcript(transcript: str, response: str, timestamp: str = None) -> Path:
    """
    Save both the user transcript and the AI response to a .txt file.

    Args:
        transcript: The ASR-generated text from the user's speech.
        response:   The LLM-generated response text.
        timestamp:  Optional timestamp string; auto-generated if None.

    Returns:
        Path to the saved transcript file.
    """
    if timestamp is None:
        timestamp = get_timestamp()

    filename = TRANSCRIPTS_DIR / f"note_{timestamp}.txt"

    content = (
        f"=== Field Note — {timestamp} ===\n\n"
        f"[USER OBSERVATION]\n{transcript}\n\n"
        f"[AI RESPONSE]\n{response}\n"
        f"{'=' * 40}\n"
    )

    try:
        filename.write_text(content, encoding="utf-8")
        return filename
    except IOError as e:
        raise IOError(f"Failed to save transcript to {filename}: {e}") from e


def banner(title: str, width: int = 50) -> None:
    """Print a decorative section banner to stdout."""
    border = "═" * width
    print(f"\n╔{border}╗")
    print(f"║  {title:<{width - 2}}║")
    print(f"╚{border}╝\n")