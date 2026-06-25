"""Speech-to-text via Groq Whisper."""

import os
from functools import lru_cache
from groq import Groq


@lru_cache(maxsize=1)
def _client() -> Groq:
    # lazy init so importing this module never fails before .env is loaded
    return Groq(api_key=os.environ["GROQ_API_KEY"])


def transcribe(audio_bytes: bytes, language: str = "en",
               model: str = "whisper-large-v3") -> str:
    res = _client().audio.transcriptions.create(
        file=("turn.wav", audio_bytes),
        model=model,
        language=language,   # ISO code improves accuracy and speed
    )
    return res.text.strip()
