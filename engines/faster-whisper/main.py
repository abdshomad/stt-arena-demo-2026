"""faster-whisper (CTranslate2) engine — real model, size selectable via modelId suffix."""
from engine_common import create_app, language_name, torch_device

SIZES = {"tiny", "base", "small", "medium", "large-v3", "large-v3-turbo"}
DEFAULT_SIZE = "small"


def variant_from_model_id(model_id: str) -> str:
    size = model_id.removeprefix("faster-whisper").lstrip("-")
    return size if size in SIZES else DEFAULT_SIZE


def load(variant: str):
    from faster_whisper import WhisperModel

    device = torch_device()
    compute_type = "float16" if device == "cuda" else "int8"
    return WhisperModel(variant, device=device, compute_type=compute_type)


def transcribe(model, wav_path, lang_code, temperature, model_id):
    seg_iter, info = model.transcribe(wav_path, language=lang_code, temperature=temperature)
    segments = []
    texts = []
    for s in seg_iter:
        segments.append({"start": float(s.start), "end": float(s.end), "text": s.text.strip()})
        texts.append(s.text.strip())
    return {
        "text": " ".join(texts),
        "language": language_name(getattr(info, "language", None), "Detected"),
        "segments": segments,
    }


app = create_app(
    engine_id="faster-whisper",
    load=load,
    transcribe=transcribe,
    variant_from_model_id=variant_from_model_id,
    default_variant=DEFAULT_SIZE,
)
