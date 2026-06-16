"""Moonshine — real UsefulSensors/moonshine-base model (English only)."""
from engine_common import create_app, torch_device

MODEL_REPO = "UsefulSensors/moonshine-base"


def load(variant: str):
    from transformers import pipeline

    return pipeline("automatic-speech-recognition", model=MODEL_REPO, device=(0 if torch_device() == "cuda" else -1))


def transcribe(pipe, wav_path, lang_code, temperature, model_id):
    # Moonshine is English-only; non-English audio yields honest garbage rather
    # than a fake success.
    out = pipe(wav_path)
    return {"text": out.get("text", ""), "language": "English", "segments": []}


app = create_app(
    engine_id="moonshine-voice",
    load=load,
    transcribe=transcribe,
)
