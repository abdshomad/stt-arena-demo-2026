"""Wav2Vec2 Indonesian/Javanese/Sundanese — real HF CTC model (no punctuation/casing)."""
from engine_common import create_app, torch_device

MODEL_REPO = "indonesian-nlp/wav2vec2-indonesian-javanese-sundanese"


def load(variant: str):
    from transformers import pipeline

    return pipeline("automatic-speech-recognition", model=MODEL_REPO, device=(0 if torch_device() == "cuda" else -1))


def transcribe(pipe, wav_path, lang_code, temperature, model_id):
    out = pipe(wav_path, chunk_length_s=20, return_timestamps="word")
    words = out.get("chunks", [])
    segments = []
    if words:
        start = float(words[0]["timestamp"][0] or 0.0)
        end = float(words[-1]["timestamp"][1] or 0.0)
        segments.append(
            {
                "start": start,
                "end": end,
                "text": out.get("text", "").strip(),
                "words": [
                    {
                        "word": w.get("text", ""),
                        "start": float(w["timestamp"][0] or 0.0),
                        "end": float(w["timestamp"][1] or 0.0),
                        "probability": 1.0,
                    }
                    for w in words
                ],
            }
        )
    return {"text": out.get("text", ""), "language": "Indonesian", "segments": segments}


app = create_app(
    engine_id="indonesian-nlp-wav2vec2-indonesian-javanese-sundanese",
    load=load,
    transcribe=transcribe,
)
