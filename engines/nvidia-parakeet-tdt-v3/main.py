"""NVIDIA Parakeet TDT 0.6B v3 — real NeMo model nvidia/parakeet-tdt-0.6b-v3."""
from engine_common import create_app, torch_device

MODEL_REPO = "nvidia/parakeet-tdt-0.6b-v3"


def load(variant: str):
    import nemo.collections.asr as nemo_asr

    device = torch_device()
    model = nemo_asr.models.ASRModel.from_pretrained(MODEL_REPO, map_location=device)
    if device == "cuda":
        model = model.cuda()
    return model


def transcribe(model, wav_path, lang_code, temperature, model_id):
    outputs = model.transcribe([wav_path], timestamps=True)
    out = outputs[0]
    text = getattr(out, "text", None) or (out if isinstance(out, str) else "")
    segments = []
    timestamps = getattr(out, "timestamp", None) or {}
    for seg in timestamps.get("segment", []):
        segments.append(
            {
                "start": float(seg.get("start", 0.0)),
                "end": float(seg.get("end", 0.0)),
                "text": seg.get("segment", "").strip(),
            }
        )
    return {"text": text, "language": None, "segments": segments}


app = create_app(
    engine_id="nvidia-parakeet-tdt-v3",
    load=load,
    transcribe=transcribe,
)
