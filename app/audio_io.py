# app/audio_io.py
# -----------------------------------------------------------
# Handles all audio I/O:
#   - Recording from microphone  (sounddevice + scipy)
#   - Loading .wav / .mp3 files  (pydub)
#   - Playing back audio          (pygame or sounddevice)
#   - Saving raw recorded audio   (scipy.io.wavfile)
# -----------------------------------------------------------

import os
import sys
import time
import wave
import tempfile
from pathlib import Path

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from app.utils import setup_logger

logger = setup_logger()


# ── Recording ─────────────────────────────────────────────────

def record_audio(
    duration: int = 10,
    sample_rate: int = 16000,
    channels: int = 1,
) -> tuple[np.ndarray, int]:
    """
    Record audio from the default microphone.

    Args:
        duration:    Maximum recording duration in seconds.
        sample_rate: Samples per second (16000 recommended for Whisper).
        channels:    Number of audio channels (1 = mono).

    Returns:
        Tuple of (audio_array as np.ndarray float32, sample_rate).

    Raises:
        RuntimeError: If sounddevice is unavailable or mic access fails.
    """
    try:
        import sounddevice as sd
    except ImportError:
        raise RuntimeError(
            "sounddevice is not installed. Run: pip install sounddevice"
        )

    logger.info(f"🎤 Recording for up to {duration} seconds... (Ctrl+C to stop early)")
    print("   Press ENTER to stop recording before the timer ends.")

    audio_chunks = []
    stopped_early = False

    def callback(indata, frames, time_info, status):
        if status:
            logger.warning(f"Audio status: {status}")
        audio_chunks.append(indata.copy())

    try:
        import threading

        stop_event = threading.Event()

        def wait_for_enter():
            try:
                input()
                stop_event.set()
            except EOFError:
                pass  # Non-interactive environment — just let timer expire

        enter_thread = threading.Thread(target=wait_for_enter, daemon=True)
        enter_thread.start()

        with sd.InputStream(
            samplerate=sample_rate,
            channels=channels,
            dtype="float32",
            callback=callback,
        ):
            start = time.time()
            while time.time() - start < duration:
                if stop_event.is_set():
                    stopped_early = True
                    break
                time.sleep(0.1)

    except sd.PortAudioError as e:
        raise RuntimeError(f"Microphone error: {e}") from e
    except KeyboardInterrupt:
        logger.info("Recording interrupted by user.")

    if not audio_chunks:
        raise RuntimeError("No audio was captured. Check microphone permissions.")

    audio_array = np.concatenate(audio_chunks, axis=0)
    audio_array = audio_array.flatten()

    elapsed = len(audio_array) / sample_rate
    logger.info(f"✅ Recorded {elapsed:.1f} seconds of audio.")
    return audio_array, sample_rate


def save_recorded_audio(
    audio_array: np.ndarray,
    sample_rate: int,
    output_path: Path = None,
) -> Path:
    """
    Save a numpy audio array to a .wav file.

    Args:
        audio_array:  Float32 numpy array of audio samples.
        sample_rate:  Sample rate in Hz.
        output_path:  Destination path; uses a temp file if None.

    Returns:
        Path to the saved .wav file.
    """
    try:
        from scipy.io import wavfile
    except ImportError:
        raise RuntimeError("scipy is not installed. Run: pip install scipy")

    if output_path is None:
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        output_path = Path(tmp.name)

    # Convert float32 → int16 for standard WAV compatibility
    audio_int16 = (audio_array * 32767).astype(np.int16)
    wavfile.write(str(output_path), sample_rate, audio_int16)
    logger.info(f"💾 Recorded audio saved: {output_path}")
    return output_path


# ── Loading ───────────────────────────────────────────────────

def load_audio_file(file_path: str | Path) -> tuple[np.ndarray, int]:
    """
    Load a .wav or .mp3 audio file into a numpy float32 array.

    Args:
        file_path: Path to the audio file.

    Returns:
        Tuple of (audio_array as np.ndarray float32, sample_rate).

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError:        If the format is unsupported.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Audio file not found: {file_path}")

    suffix = file_path.suffix.lower()
    logger.info(f"📂 Loading audio file: {file_path}")

    if suffix == ".wav":
        try:
            from scipy.io import wavfile
            sample_rate, data = wavfile.read(str(file_path))

            # Normalize to float32
            if data.dtype == np.int16:
                audio = data.astype(np.float32) / 32768.0
            elif data.dtype == np.int32:
                audio = data.astype(np.float32) / 2147483648.0
            elif data.dtype == np.float32:
                audio = data
            else:
                audio = data.astype(np.float32)

            # Convert stereo → mono
            if audio.ndim == 2:
                audio = audio.mean(axis=1)

            logger.info(f"✅ WAV loaded: {sample_rate} Hz, {len(audio)/sample_rate:.1f}s")
            return audio, sample_rate

        except Exception as e:
            raise ValueError(f"Failed to load WAV file: {e}") from e

    elif suffix == ".mp3":
        try:
            from pydub import AudioSegment
            seg = AudioSegment.from_mp3(str(file_path))
            seg = seg.set_channels(1).set_frame_rate(16000)
            samples = np.array(seg.get_array_of_samples(), dtype=np.float32)
            samples /= 2**15  # int16 → float32
            logger.info(f"✅ MP3 loaded: {seg.frame_rate} Hz, {len(samples)/seg.frame_rate:.1f}s")
            return samples, seg.frame_rate
        except Exception as e:
            raise ValueError(f"Failed to load MP3 file: {e}") from e

    else:
        raise ValueError(f"Unsupported audio format: {suffix}. Use .wav or .mp3")


# ── Playback ──────────────────────────────────────────────────

def play_audio_file(file_path: str | Path) -> None:
    """
    Play an audio file using pygame (preferred) or sounddevice as fallback.

    Args:
        file_path: Path to the .mp3 or .wav file to play.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        logger.warning(f"⚠️ Audio file not found for playback: {file_path}")
        return

    logger.info(f"🔊 Playing: {file_path.name}")

    # Method 1: pygame (best cross-platform for mp3)
    try:
        import pygame
        pygame.mixer.init()
        pygame.mixer.music.load(str(file_path))
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
        pygame.mixer.quit()
        return
    except Exception as e:
        logger.debug(f"pygame playback failed ({e}), trying sounddevice...")

    # Method 2: sounddevice fallback (wav only)
    try:
        import sounddevice as sd
        from scipy.io import wavfile

        if file_path.suffix.lower() == ".wav":
            sr, data = wavfile.read(str(file_path))
            if data.dtype == np.int16:
                data = data.astype(np.float32) / 32768.0
            sd.play(data, sr)
            sd.wait()
            return
    except Exception as e:
        logger.debug(f"sounddevice playback failed: {e}")

    logger.warning("⚠️ Could not play audio automatically. Open the file manually.")