"""
MedBhasha Text-to-Speech (TTS) Service
Synthesizes vernacular spoken summaries using Microsoft Edge Neural TTS voices
for Indian languages, with a Gemini TTS fallback for languages that Edge TTS
does not support (notably Odia).
"""

from __future__ import annotations

import asyncio
import base64
import io
import logging
import os
import re
import wave
from typing import Dict, Tuple

from dotenv import load_dotenv
from google import genai
from google.genai import types

import edge_tts

load_dotenv()
logger = logging.getLogger("medbhasha.tts_service")

VOICE_MAP: Dict[str, str] = {
    "hi": "hi-IN-SwaraNeural",
    "bn": "bn-IN-TanishaaNeural",
    "ta": "ta-IN-PallaviNeural",
    "en": "en-IN-NeerjaNeural",
}

DEFAULT_FALLBACK_VOICE = "en-IN-NeerjaNeural"

GEMINI_TTS_MODEL = os.getenv("GEMINI_TTS_MODEL", "gemini-3.8-flash-tts")
GEMINI_TTS_FALLBACK_MODELS = [
    m.strip()
    for m in os.getenv(
        "GEMINI_TTS_FALLBACK_MODELS",
        "gemini-3.8-flash-tts,gemini-3.1-flash-tts-preview",
    ).split(",")
    if m.strip()
]
GEMINI_TTS_VOICE = os.getenv("GEMINI_TTS_VOICE", "Kore")


def get_voice_for_language(language_code: str) -> str:
    clean_lang = language_code.lower().strip()
    return VOICE_MAP.get(clean_lang, DEFAULT_FALLBACK_VOICE)


def _pcm_to_wav(pcm: bytes, sample_rate: int, channels: int = 1, sample_width: int = 2) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(channels)
        w.setsampwidth(sample_width)
        w.setframerate(sample_rate)
        w.writeframes(pcm)
    return buf.getvalue()


def _parse_rate_from_mime(mime: str) -> int:
    match = re.search(r"rate=(\d+)", mime or "")
    return int(match.group(1)) if match else 24000


async def _synthesize_with_edge(text: str, language: str) -> Tuple[bytes, str]:
    voice = get_voice_for_language(language)
    communicate = edge_tts.Communicate(text=text.strip(), voice=voice)
    audio_buffer = io.BytesIO()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_buffer.write(chunk["data"])
    audio_buffer.seek(0)
    data = audio_buffer.getvalue()
    if not data:
        raise RuntimeError("Audio stream produced zero bytes.")
    return data, "audio/mpeg"


async def _synthesize_with_gemini(text: str, language: str) -> Tuple[bytes, str]:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "your-gemini-api-key-here":
        raise RuntimeError("GEMINI_API_KEY not configured for TTS fallback.")
    client = genai.Client(api_key=api_key, http_options={"timeout": 90000})

    last_exc: Exception | None = None
    for model in GEMINI_TTS_FALLBACK_MODELS:
        try:
            response = await asyncio.to_thread(
                client.models.generate_content,
                model=model,
                contents=text.strip(),
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                voice_name=GEMINI_TTS_VOICE
                            )
                        )
                    ),
                ),
            )
            part = response.candidates[0].content.parts[0]
            data = part.inline_data.data
            if isinstance(data, str):
                data = base64.b64decode(data)
            mime = part.inline_data.mime_type or "audio/wav"
            if "l16" in mime or "pcm" in mime:
                rate = _parse_rate_from_mime(mime)
                wav = _pcm_to_wav(data, rate)
                return wav, "audio/wav"
            return data, mime.split(";")[0].strip() or "audio/wav"
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            logger.warning("Gemini TTS model=%s failed: %s", model, exc)
            continue
    if last_exc is not None:
        raise last_exc
    raise RuntimeError("No Gemini TTS models available.")


async def synthesize_speech_stream(text: str, language: str = "hi") -> Tuple[io.BytesIO, str]:
    if not text or not text.strip():
        raise ValueError("Text for speech synthesis cannot be empty.")

    clean_lang = language.lower().strip()
    media_type = "audio/mpeg"

    # Odia has no Edge TTS voice: use Gemini TTS directly.
    if clean_lang == "or":
        try:
            data, media_type = await _synthesize_with_gemini(text, clean_lang)
            buf = io.BytesIO(data)
            buf.seek(0)
            return buf, media_type
        except Exception as exc:  # noqa: BLE001
            logger.warning("Odia Gemini TTS failed: %s. Falling back to Hindi Edge voice.", exc)
            try:
                data, media_type = await _synthesize_with_edge(text, "hi")
                buf = io.BytesIO(data)
                buf.seek(0)
                return buf, media_type
            except Exception as exc2:  # noqa: BLE001
                raise RuntimeError(f"TTS synthesis failed: {exc2}") from exc2

    # Primary: Edge TTS for languages with a dedicated voice.
    try:
        data, media_type = await _synthesize_with_edge(text, clean_lang)
        buf = io.BytesIO(data)
        buf.seek(0)
        return buf, media_type
    except Exception as exc:  # noqa: BLE001
        logger.warning("Edge TTS failed for %s: %s. Trying Gemini TTS.", clean_lang, exc)
        try:
            data, media_type = await _synthesize_with_gemini(text, clean_lang)
            buf = io.BytesIO(data)
            buf.seek(0)
            return buf, media_type
        except Exception as exc2:  # noqa: BLE001
            raise RuntimeError(f"TTS synthesis failed: {exc2}") from exc2