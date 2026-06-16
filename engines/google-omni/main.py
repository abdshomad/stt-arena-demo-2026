"""'Google Omni' is fictional — backed by the real Gemini API (audio understanding).

Available only when GEMINI_API_KEY is set in .secrets; otherwise reports N/A.
"""
import base64
import os

from engine_common import create_app

GEMINI_MODEL = os.getenv("GOOGLE_OMNI_GEMINI_MODEL", "gemini-2.5-flash")
PROMPT = "Transcribe this audio verbatim. Reply with only the transcript text, nothing else."


def check():
    if not os.getenv("GEMINI_API_KEY"):
        return False, "GEMINI_API_KEY not set in .secrets"
    return True, None


def transcribe(_model, wav_path, lang_code, temperature, model_id):
    import requests

    with open(wav_path, "rb") as fh:
        audio_b64 = base64.b64encode(fh.read()).decode()
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
        f"?key={os.environ['GEMINI_API_KEY']}"
    )
    body = {
        "contents": [
            {
                "parts": [
                    {"text": PROMPT},
                    {"inline_data": {"mime_type": "audio/wav", "data": audio_b64}},
                ]
            }
        ]
    }
    resp = requests.post(url, json=body, timeout=300)
    resp.raise_for_status()
    payload = resp.json()
    text = payload["candidates"][0]["content"]["parts"][0]["text"].strip()
    return {"text": text, "language": None, "segments": []}


app = create_app(
    engine_id="google-omni",
    load=None,
    transcribe=transcribe,
    check=check,
)
