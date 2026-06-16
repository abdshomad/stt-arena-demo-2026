"""'Microsoft Vibe-Voice ASR' — VibeVoice is a TTS model, not STT. Backed by the
real Azure AI Speech fast transcription API.

Available only when AZURE_SPEECH_KEY and AZURE_SPEECH_REGION are set in .secrets.
"""
import json
import os

from engine_common import create_app

LOCALES = {
    "en": "en-US",
    "id": "id-ID",
    "jv": "jv-ID",
    "su": "su-ID",
    "fr": "fr-FR",
    "de": "de-DE",
    "es": "es-ES",
    "ja": "ja-JP",
    "zh": "zh-CN",
}


def check():
    if not os.getenv("AZURE_SPEECH_KEY") or not os.getenv("AZURE_SPEECH_REGION"):
        return False, "AZURE_SPEECH_KEY / AZURE_SPEECH_REGION not set in .secrets (VibeVoice is TTS-only; Azure Speech is used)"
    return True, None


def transcribe(_model, wav_path, lang_code, temperature, model_id):
    import requests

    region = os.environ["AZURE_SPEECH_REGION"]
    url = (
        f"https://{region}.api.cognitive.microsoft.com/speechtotext/transcriptions:transcribe"
        "?api-version=2024-11-15"
    )
    definition = {"locales": [LOCALES.get(lang_code or "en", "en-US")]}
    with open(wav_path, "rb") as fh:
        resp = requests.post(
            url,
            headers={"Ocp-Apim-Subscription-Key": os.environ["AZURE_SPEECH_KEY"]},
            files={
                "audio": ("audio.wav", fh, "audio/wav"),
                "definition": (None, json.dumps(definition), "application/json"),
            },
            timeout=300,
        )
    resp.raise_for_status()
    payload = resp.json()
    phrases = payload.get("combinedPhrases", [])
    text = phrases[0].get("text", "") if phrases else ""
    segments = [
        {
            "start": p.get("offsetMilliseconds", 0) / 1000.0,
            "end": (p.get("offsetMilliseconds", 0) + p.get("durationMilliseconds", 0)) / 1000.0,
            "text": p.get("text", ""),
            "speakerId": p.get("speaker", 0) or 0,
        }
        for p in payload.get("phrases", [])
    ]
    return {"text": text, "language": None, "segments": segments}


app = create_app(
    engine_id="microsoft-vibe-voice-asr",
    load=None,
    transcribe=transcribe,
    check=check,
)
