# 🎙️ Voice Interview Agent

A voice-based mock-interview agent. You speak; it transcribes you (STT), grounds
itself in a fixed reference Q&A set, uses an LLM to act as an adaptive
interviewer (follow-ups, coaching, no answer-leaking), speaks back (TTS), and
gives structured feedback at the end. Configurable in **English, Hindi, and
German**.

## Pipeline

```
mic ──► Groq Whisper (STT) ──► Retriever (reference Q&A)
     ──► Groq LLaMA 3.3 (grade + next line) ──► TTS (ElevenLabs / gTTS) ──► audio
end ──► structured feedback (score, strengths, improvements, recommendation)
```

## Tech choices (short version)

| Stage   | Choice | Why |
|---------|--------|-----|
| STT     | Groq `whisper-large-v3` | one provider with the LLM = one auth, fewer hops, fast |
| Retrieval | `sentence-transformers` MiniLM + brute-force cosine | only 8–12 vectors; an ANN index (FAISS) adds cost with zero recall benefit |
| LLM     | Groq `llama-3.3-70b-versatile` | Groq's speed is what makes voice feel responsive; JSON mode for reliable grading |
| TTS     | ElevenLabs `eleven_multilingual_v2`, gTTS fallback | best multilingual quality, but still runs free without a key |
| UI      | Streamlit (`audio_input` + `audio` autoplay) | mic + playback with no extra components |

See `ARCHITECTURE.md` for the full reasoning (retrieval, grounding, latency).

## Setup

You need **Python 3.11+** and a free **Groq API key** (https://console.groq.com).
An ElevenLabs key is optional — without it the app uses free gTTS voices.

### Windows (PowerShell)

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env      # then open .env and paste your GROQ_API_KEY
streamlit run app.py
```

### macOS / Linux

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # then edit .env and paste your GROQ_API_KEY
streamlit run app.py
```

The app opens at http://localhost:8501. Click **Start interview**, allow mic
access, and answer out loud.

> First run downloads the MiniLM embedding model (~90 MB) once.

## Adding or editing questions (three ways, no code changes)

The reference Q&A is fully decoupled from the interview logic. You can update it
without touching anything in `core/`:

1. **Edit the YAML** — open `questions/software_engineer.yaml`, copy any block,
   fill in `id`, `question`, `ideal_answer`, and `key_points`. Comments are
   preserved. Changes hot-reload in the running app (no restart).
2. **Use the in-app editor** — on the start screen, expand *"Edit interview
   questions"* and use the grid: edit any cell, add a row with ➕, delete with
   the trash icon, then **Save changes**. Writes straight back to the YAML.
3. **Add a whole new set** — drop a new `*.yaml` into `questions/`. It appears
   in the sidebar **Question set** dropdown automatically (auto-discovery).
   `questions/customer_support.yaml` is included as a live example.

All three go through one module, `core/qa_store.py`, which validates the data
and surfaces a clear error if a required field is missing.

## Configuration

Everything tweakable lives in `config.yaml`: language, question set,
`max_attempts` (follow-ups per question), model names, and TTS provider/voice.
Language is also switchable live from the sidebar.

## Project layout

```
voice-interview-agent/
├── app.py                 # Streamlit UI + pipeline wiring
├── config.yaml            # all settings
├── questions/
│   └── software_engineer.yaml   # the reference Q&A bank (edit freely)
├── core/
│   ├── retriever.py       # embeds + searches the Q&A bank
│   ├── stt.py             # Groq Whisper
│   ├── tts.py             # ElevenLabs + gTTS fallback
│   ├── interviewer.py     # grounded adaptive turn controller
│   └── feedback.py        # end-of-interview report
├── requirements.txt
├── .env.example
└── ARCHITECTURE.md
```

## Known limitations (prototype)

- Recording is push-to-record (click start/stop), not continuous streaming with
  voice-activity detection. Fine for a prototype; noted in the architecture doc.
- Audio plays after the full TTS clip is generated (no token-by-token streaming).
  See `ARCHITECTURE.md` for how the latency would be reduced.
