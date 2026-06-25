"""Text-to-speech. ElevenLabs (multilingual) with a free gTTS fallback so the
project runs even without an ElevenLabs key."""

import io
import os

_GTTS_LANG = {"en": "en", "hi": "hi", "de": "de"}


def synthesize(text: str, cfg: dict, language: str = "en") -> tuple[bytes, str]:
    """Return (audio_bytes, mime_type)."""
    if cfg.get("provider") == "elevenlabs" and os.environ.get("ELEVENLABS_API_KEY"):
        try:
            from elevenlabs.client import ElevenLabs
            from elevenlabs import VoiceSettings
            client = ElevenLabs(api_key=os.environ["ELEVENLABS_API_KEY"])
            s = cfg.get("settings", {})
            stream = client.text_to_speech.convert(
                voice_id=cfg["voice_id"],
                model_id=cfg["model"],
                text=text,
                voice_settings=VoiceSettings(
                    stability=s.get("stability", 0.4),
                    similarity_boost=s.get("similarity_boost", 0.75),
                    style=s.get("style", 0.45),
                    use_speaker_boost=s.get("use_speaker_boost", True),
                ),
            )
            return b"".join(stream), "audio/mp3"
        except Exception as e:
            print(f"[tts] ElevenLabs failed, falling back to gTTS: {e}")

    # fallback: gTTS (free, no key)
    from gtts import gTTS
    buf = io.BytesIO()
    gTTS(text=text, lang=_GTTS_LANG.get(language, "en")).write_to_fp(buf)
    return buf.getvalue(), "audio/mp3"
