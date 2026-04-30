# app/main.py
# -----------------------------------------------------------
# Entry point for the Voice AI Field Notes Assistant.
#
# Pipeline:
#   1. Parse CLI arguments
#   2. Load .env
#   3. Get audio (mic recording OR file load)
#   4. ASR → transcript
#   5. LLM → response
#   6. TTS → audio
#   7. Playback + save transcript
# -----------------------------------------------------------

import os
import sys
import argparse
from pathlib import Path

# Ensure project root is on the path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Load .env before importing config/settings
try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=ROOT / ".env")
except ImportError:
    print("[WARN] python-dotenv not installed. .env file will NOT be loaded.")
    print("       Install with: pip install python-dotenv")

from config.settings import (
    RECORD_DURATION,
    RECORD_SAMPLE_RATE,
    RECORD_CHANNELS,
)
from app.utils  import setup_logger, get_timestamp, save_transcript, banner
from app.audio_io import record_audio, load_audio_file, play_audio_file, save_recorded_audio
from app.asr     import transcribe
from app.llm     import generate_response
from app.tts     import text_to_speech

logger = setup_logger()


# ── CLI ───────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="🎙️  Voice AI Field Notes Assistant",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python app/main.py                          # Record from mic\n"
            "  python app/main.py --file data/sample_audio/note.wav\n"
            "  python app/main.py --duration 15            # Record 15 seconds\n"
            "  python app/main.py --no-play                # Skip audio playback\n"
            "  python app/main.py --text-only              # Skip TTS entirely\n"
        ),
    )
    parser.add_argument(
        "--file", "-f",
        type=str,
        default=None,
        help="Path to an existing .wav or .mp3 audio file (skips mic recording)",
    )
    parser.add_argument(
        "--duration", "-d",
        type=int,
        default=RECORD_DURATION,
        help=f"Microphone recording duration in seconds (default: {RECORD_DURATION})",
    )
    parser.add_argument(
        "--no-play",
        action="store_true",
        help="Save TTS audio but do NOT play it back",
    )
    parser.add_argument(
        "--text-only",
        action="store_true",
        help="Skip TTS — only show transcript and LLM response as text",
    )
    parser.add_argument(
        "--save-recording",
        action="store_true",
        help="Save mic recording to outputs/audio/ (for debugging)",
    )
    return parser.parse_args()


# ── Pipeline steps ────────────────────────────────────────────

def step_get_audio(args) -> tuple:
    """
    Step 1: Obtain audio either from file or microphone.
    Returns (audio_array, sample_rate, source_label).
    """
    if args.file:
        file_path = Path(args.file)
        audio, sr = load_audio_file(file_path)
        return audio, sr, f"file:{file_path.name}"
    else:
        audio, sr = record_audio(
            duration=args.duration,
            sample_rate=RECORD_SAMPLE_RATE,
            channels=RECORD_CHANNELS,
        )
        return audio, sr, "microphone"


def step_transcribe(audio, sample_rate: int) -> str:
    """Step 2: Run ASR on audio array."""
    return transcribe(audio, sample_rate=sample_rate)


def step_llm(transcript: str) -> str:
    """Step 3: Generate LLM response from transcript."""
    return generate_response(transcript)


def step_tts(response_text: str, timestamp: str, args) -> Path | None:
    """Step 4: Convert response to speech and optionally play it."""
    if args.text_only:
        logger.info("ℹ️  --text-only: skipping TTS.")
        return None

    audio_file = text_to_speech(response_text, timestamp=timestamp)

    if not args.no_play:
        play_audio_file(audio_file)
    else:
        logger.info(f"ℹ️  --no-play: audio saved at {audio_file}")

    return audio_file


def step_save(transcript: str, response: str, timestamp: str) -> Path:
    """Step 5: Persist transcript + response to disk."""
    return save_transcript(transcript, response, timestamp)


# ── Main ──────────────────────────────────────────────────────

def main():
    banner("🌿 Voice AI Field Notes Assistant")
    args = parse_args()
    timestamp = get_timestamp()

    print(f"  Mode:      {'File: ' + args.file if args.file else 'Microphone'}")
    print(f"  Duration:  {args.duration}s (mic mode)")
    print(f"  TTS:       {'disabled' if args.text_only else 'enabled'}")
    print(f"  Playback:  {'disabled' if args.no_play else 'enabled'}")
    print()

    # ── Step 1: Audio input ───────────────────────────────────
    banner("Step 1 — Audio Input")
    try:
        audio, sample_rate, source = step_get_audio(args)
        print(f"  Source: {source}")

        if args.save_recording and source == "microphone":
            from config.settings import AUDIO_OUT_DIR
            rec_path = AUDIO_OUT_DIR / f"recording_{timestamp}.wav"
            save_recorded_audio(audio, sample_rate, rec_path)
            print(f"  Recording saved: {rec_path}")

    except (FileNotFoundError, ValueError, RuntimeError) as e:
        logger.error(f"❌ Audio input failed: {e}")
        sys.exit(1)

    # ── Step 2: Transcription ─────────────────────────────────
    banner("Step 2 — Speech Recognition")
    try:
        transcript = step_transcribe(audio, sample_rate)
        print(f"\n  📝 You said:\n     \"{transcript}\"\n")
    except RuntimeError as e:
        logger.error(f"❌ Transcription failed: {e}")
        sys.exit(1)

    # ── Step 3: LLM response ──────────────────────────────────
    banner("Step 3 — AI Response")
    response = step_llm(transcript)
    print(f"\n  🤖 Assistant:\n")
    # Pretty-print wrapped at 70 chars
    import textwrap
    for line in response.split("\n"):
        print(textwrap.fill("     " + line, width=74))
    print()

    # ── Step 4: TTS ───────────────────────────────────────────
    banner("Step 4 — Text-to-Speech")
    audio_file = step_tts(response, timestamp, args)

    # ── Step 5: Save transcript ───────────────────────────────
    banner("Step 5 — Saving Notes")
    transcript_file = step_save(transcript, response, timestamp)
    print(f"  📄 Transcript saved: {transcript_file}")
    if audio_file:
        print(f"  🔊 Audio response:   {audio_file}")

    banner("✅ Done")
    print("  Your field note has been captured, processed, and saved.\n")


if __name__ == "__main__":
    main()