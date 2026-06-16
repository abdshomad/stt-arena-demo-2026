"""OpenAI Whisper engine — real model, size selectable via modelId suffix."""
from engine_common import create_app, language_name, torch_device

SIZES = {"tiny", "base", "small", "medium", "large-v3", "large-v3-turbo"}
DEFAULT_SIZE = "small"


def variant_from_model_id(model_id: str) -> str:
    size = model_id.removeprefix("whisper").lstrip("-")
    return size if size in SIZES else DEFAULT_SIZE


def load(variant: str):
    import whisper

    return whisper.load_model(variant, device=torch_device())


def transcribe(model, wav_path, lang_code, temperature, model_id):
    fp16 = torch_device() == "cuda"
    result = model.transcribe(wav_path, language=lang_code, temperature=temperature, fp16=fp16)
    segments = [
        {"start": float(s.get("start", 0.0)), "end": float(s.get("end", 0.0)), "text": s.get("text", "").strip()}
        for s in result.get("segments", [])
    ]
    return {
        "text": result.get("text", ""),
        "language": language_name(result.get("language"), "Detected"),
        "segments": segments,
    }


app = create_app(
    engine_id="whisper",
    load=load,
    transcribe=transcribe,
    variant_from_model_id=variant_from_model_id,
    default_variant=DEFAULT_SIZE,
)
