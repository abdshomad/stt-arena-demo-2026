"""Cahya Whisper Small ID — real HF model cahya/whisper-small-id (Indonesian fine-tune)."""
from engine_common import create_app, torch_device

MODEL_REPO = "cahya/whisper-small-id"


def load(variant: str):
    from transformers import pipeline

    return pipeline(
        "automatic-speech-recognition",
        model=MODEL_REPO,
        device=(0 if torch_device() == "cuda" else -1),
        chunk_length_s=30,
    )


def transcribe(pipe, wav_path, lang_code, temperature, model_id):
    try:
        out = pipe(wav_path, return_timestamps=True, generate_kwargs={"task": "transcribe"})
    except Exception:
        # Older fine-tunes lack timestamp- and task-ready generation configs
        out = pipe(wav_path)
    segments = []
    for chunk in out.get("chunks", []):
        ts = chunk.get("timestamp") or (0.0, 0.0)
        segments.append(
            {
                "start": float(ts[0] or 0.0),
                "end": float(ts[1] or ts[0] or 0.0),
                "text": chunk.get("text", "").strip(),
            }
        )
    return {"text": out.get("text", ""), "language": "Indonesian", "segments": segments}


app = create_app(
    engine_id="cahya-whisper-small-id",
    load=load,
    transcribe=transcribe,
)
