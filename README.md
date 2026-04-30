# 🌿 Voice AI Field Notes Assistant

> A production-ready Voice AI pipeline that records or loads audio, transcribes speech with Whisper, enriches observations with Groq LLM, and reads the response back aloud — built for field researchers, scientists, and journalists.

---

---

## ✨ Features

|    | Feature                             | Detail                                                                |
| -- | ----------------------------------- | --------------------------------------------------------------------- |
| 🎤 | **Live microphone recording** | Captures real-time audio from your default mic                        |
| 📂 | **Audio file input**          | Load any `.wav`or `.mp3`file for processing                       |
| 🧠 | **Local speech recognition**  | Powered by `faster-whisper`— runs fully offline                    |
| 🤖 | **Intelligent LLM responses** | Groq API (`llama-3.1-8b-instant`) with structured field note output |
| 🔄 | **Offline fallback**          | Rule-based keyword matching when Groq API is unavailable              |
| 🔊 | **Text-to-speech playback**   | `gTTS`(online) with `pyttsx3`offline fallback                     |
| 💾 | **Auto-save everything**      | Transcripts →`outputs/transcripts/`, audio →`outputs/audio/`    |
| 🧱 | **Modular architecture**      | Every component is independently testable and swappable               |

## 📁 Project Structure


```
voice-ai-app/
│
├── app/
│   ├── main.py        ← Pipeline entry point — orchestrates all steps
│   ├── asr.py         ← Whisper speech-to-text (faster-whisper + fallback)
│   ├── tts.py         ← Text-to-speech (gTTS + pyttsx3 fallback)
│   ├── llm.py         ← Groq API integration + rule-based fallback
│   ├── audio_io.py    ← Mic recording, audio loading, playback
│   └── utils.py       ← Logging, timestamps, transcript saving
│
├── config/
│   └── settings.py    ← All configuration in one place
│
├── data/
│   └── sample_audio/  ← Drop your .wav / .mp3 test files here
│
├── outputs/
│   ├── transcripts/   ← Auto-generated .txt note files
│   └── audio/         ← Auto-generated TTS .mp3 response files
│
├── .env               ← Your API key (never commit this)
├── requirements.txt
├── README.md
└── .gitignore
```


## ⚙️ Setup

### Prerequisites

* **Python 3.10 or higher**
* **ffmpeg** — required for MP3 audio processing
* **PortAudio** — required for microphone access

Install system tools:

bash

```bash
# macOS
brew install ffmpeg portaudio

# Ubuntu / Debian
sudoaptinstall ffmpeg portaudio19-dev

# Windows (PowerShell, run as admin)
winget install ffmpeg
```

---

### Step 1 — Clone and enter the project

bash

```bash
cd voice-ai-app
```

### Step 2 — Create a virtual environment

bash

```bash
python -m venv venv

# macOS / Linux
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### Step 3 — Install Python dependencies

bash

```bash
pip install -r requirements.txt
```

> **Note:** If `faster-whisper` fails to install, the app will automatically fall back to `openai-whisper`. You can install it manually with:
>
> bash
>
> ```bash
> pip install openai-whisper
> ```

### Step 4 — Configure your Groq API key

1. Sign up for a **free** account at [console.groq.com](https://console.groq.com)
2. Create an API key
3. Create a `.env` file in the project root:

bash

```bash
# .env
GROQ_API_KEY=your_actual_api_key_here
```

> ⚠️ Never commit your `.env` file. It is already listed in `.gitignore`.

> **No Groq key?** The app still works — it uses built-in rule-based responses as a fallback. No API required.

---

## 🚀 Running the App

All commands should be run from inside the `voice-ai-app/` directory with your virtual environment active.

### Record from microphone (default — 10 seconds)

bash

```bash
python app/main.py
```

Press **ENTER** to stop recording before the timer ends.

---

### Load an existing audio file

bash

```bash
python app/main.py --file data/sample_audio/my_note.wav
python app/main.py --file data/sample_audio/observation.mp3
```

---

### Custom recording duration

bash

```bash
python app/main.py --duration 20
```

---

### Skip audio playback (save only)

bash

```bash
python app/main.py --no-play
```

---

### Text-only mode (no TTS generated)

bash

```bash
python app/main.py --text-only
```

---

### Save the mic recording to disk (for debugging)

bash

```bash
python app/main.py --save-recording
```

---

### Combine flags

bash

```bash
# Load file, no playback
python app/main.py --file data/sample_audio/note.wav --no-play

# 30-second recording, text output only
python app/main.py --duration 30 --text-only
```

---

## 💬 Example Session

```
╔══════════════════════════════════════════════════════╗
║  🌿 Voice AI Field Notes Assistant                   ║
╚══════════════════════════════════════════════════════╝

  Mode:      Microphone
  Duration:  10s
  TTS:       enabled
  Playback:  enabled

╔══════════════════════════════════════════════════════╗
║  Step 1 — Audio Input                                ║
╚══════════════════════════════════════════════════════╝
🎤 Recording for up to 10 seconds...
   Press ENTER to stop recording before the timer ends.
✅ Recorded 7.4 seconds of audio.

╔══════════════════════════════════════════════════════╗
║  Step 2 — Speech Recognition                         ║
╚══════════════════════════════════════════════════════╝

  📝 You said:
     "Spotted a red-tailed hawk nesting near the north ridge,
      approximately 200 meters from the main stream."

╔══════════════════════════════════════════════════════╗
║  Step 3 — AI Response                                ║
╚══════════════════════════════════════════════════════╝

  🤖 Assistant:

     Excellent observation! Red-tailed hawks are highly territorial
     during nesting season. Consider documenting: Is this an active
     nest with eggs or fledglings? What is the approximate nest height
     and tree species? Any signs of a second adult nearby?

     [SUMMARY] Red-tailed hawk nest sighted at north ridge, ~200m from
     stream. Recommend follow-up visit to confirm nesting stage and
     record GPS coordinates.

╔══════════════════════════════════════════════════════╗
║  Step 5 — Saving Notes                               ║
╚══════════════════════════════════════════════════════╝
  📄 Transcript saved: outputs/transcripts/note_20240615_143022.txt
  🔊 Audio response:   outputs/audio/response_20240615_143022.mp3

╔══════════════════════════════════════════════════════╗
║  ✅ Done                                             ║
╚══════════════════════════════════════════════════════╝
```

## 🔧 Configuration

All settings live in `config/settings.py`. Edit this file to change behavior without touching application code.

| Setting                | Default                    | Description                                                 |
| ---------------------- | -------------------------- | ----------------------------------------------------------- |
| `WHISPER_MODEL_SIZE` | `"base"`                 | Model size:`tiny`/`base`/`small`/`medium`/`large` |
| `WHISPER_DEVICE`     | `"cpu"`                  | Use `"cuda"`for GPU acceleration                          |
| `RECORD_DURATION`    | `10`                     | Default microphone recording length (seconds)               |
| `GROQ_MODEL`         | `"llama-3.1-8b-instant"` | Groq LLM model name                                         |
| `LLM_MAX_TOKENS`     | `512`                    | Maximum tokens in LLM response                              |
| `TTS_LANGUAGE`       | `"en"`                   | gTTS language code                                          |

> **Whisper model sizes** — larger = more accurate, slower to load:
> `tiny` (fastest) → `base` → `small` → `medium` → `large` (most accurate)

---

## 🛠️ Troubleshooting

| Problem                              | Likely Cause          | Fix                                   |
| ------------------------------------ | --------------------- | ------------------------------------- |
| `ModuleNotFoundError: sounddevice` | Not installed         | `pip install sounddevice`           |
| `OSError: PortAudio not found`     | System dep missing    | Install PortAudio (see Setup)         |
| `ffmpeg not found`                 | System dep missing    | Install ffmpeg (see Setup)            |
| `GROQ_API_KEY not found`           | Missing `.env`      | Create `.env`with your key          |
| Empty transcript                     | Too quiet / no speech | Speak louder, or use `--file`       |
| `gTTS`fails                        | No internet           | pyttsx3 auto-activates as fallback    |
| `faster-whisper`install fails      | Build tools missing   | `pip install openai-whisper`instead |
| Mic records silence                  | Wrong input device    | Check system default mic settings     |

## 🧱 Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    app/main.py                          │
│              (Pipeline Orchestrator)                    │
└──────────┬─────────┬──────────┬─────────────┬──────────┘
           │         │          │             │
    ┌──────▼──┐ ┌────▼────┐ ┌──▼────┐ ┌──────▼──────┐
    │audio_io │ │  asr.py │ │llm.py │ │   tts.py    │
    │         │ │         │ │       │ │             │
    │ Record  │ │ Whisper │ │ Groq  │ │ gTTS        │
    │ Load    │ │ (local) │ │  API  │ │ + pyttsx3   │
    │ Play    │ │         │ │   +   │ │ fallback    │
    └─────────┘ └─────────┘ │fallbk │ └─────────────┘
                             └───────┘
           │                              │
    ┌──────▼──────────────────────────────▼──────┐
    │                 utils.py                   │
    │     (Logging · Timestamps · Save files)    │
    └────────────────────────────────────────────┘
                         │
    ┌────────────────────▼───────────────────────┐
    │              config/settings.py            │
    │   (All paths, model names, parameters)     │
    └────────────────────────────────────────────┘
```

## 📄 License

MIT License — free for personal and commercial use.
