"""NVIDIA MultiTalker ASR — real NeMo model nvidia/multitalker-parakeet-streaming-0.6b-v1."""
from engine_common import create_app, torch_device

MODEL_REPO = "nvidia/multitalker-parakeet-streaming-0.6b-v1"


def load(variant: str):
    import nemo.collections.asr as nemo_asr

    device = torch_device()
    model = nemo_asr.models.ASRModel.from_pretrained(MODEL_REPO, map_location=device)
    if device == "cuda":
        model = model.cuda()
    return model


def transcribe(model, wav_path, lang_code, temperature, model_id):
    outputs = model.transcribe([wav_path])
    out = outputs[0]
    text = getattr(out, "text", None) or (out if isinstance(out, str) else "")
    return {"text": text, "language": "en", "segments": []}


app = create_app(
    engine_id="nvidia-multitalker-asr",
    load=load,
    transcribe=transcribe,
)
