"""'GPT Realtime Whisper' — backed by the real OpenAI transcription API.

Available only when OPENAI_API_KEY is set in .secrets; otherwise reports N/A.
"""
import os

from engine_common import create_app

API_URL = "https://api.openai.com/v1/audio/transcriptions"
API_MODEL = os.getenv("OPENAI_TRANSCRIBE_MODEL", "gpt-4o-transcribe")


def check():
    if not os.getenv("OPENAI_API_KEY"):
        return False, "OPENAI_API_KEY not set in .secrets"
    return True, None


def transcribe(_model, wav_path, lang_code, temperature, model_id):
    import requests

    headers = {"Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}"}
    data = {"model": API_MODEL, "temperature": str(temperature)}
    if lang_code:
        data["language"] = lang_code
    with open(wav_path, "rb") as fh:
        resp = requests.post(
            API_URL,
            headers=headers,
            data=data,
            files={"file": ("audio.wav", fh, "audio/wav")},
            timeout=300,
        )
    resp.raise_for_status()
    payload = resp.json()
    return {"text": payload.get("text", ""), "language": None, "segments": []}


app = create_app(
    engine_id="gpt-realtime-whisper",
    load=None,
    transcribe=transcribe,
    check=check,
)
