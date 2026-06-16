"""NVIDIA Nemotron Speech Streaming 0.6B — real NeMo model nvidia/nemotron-speech-streaming-en-0.6b."""
from engine_common import create_app, torch_device

MODEL_REPO = "nvidia/nemotron-speech-streaming-en-0.6b"


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
    engine_id="nvidia-nemotron-speech-streaming-en",
    load=load,
    transcribe=transcribe,
)
