"""WhisperX engine — real model with optional pyannote diarization (needs HF_TOKEN)."""
import os

from engine_common import create_app, language_name, torch_device

SIZES = {"tiny", "base", "small", "medium", "large-v3"}
DEFAULT_SIZE = "small"
HF_TOKEN = os.getenv("HF_TOKEN")


def variant_from_model_id(model_id: str) -> str:
    size = model_id.removeprefix("whisperx").lstrip("-")
    return size if size in SIZES else DEFAULT_SIZE


def load(variant: str):
    import whisperx

    device = torch_device()
    compute_type = "float16" if device == "cuda" else "int8"
    model = whisperx.load_model(variant, device, compute_type=compute_type)
    diarizer = None
    if HF_TOKEN:
        try:
            diarizer = whisperx.DiarizationPipeline(use_auth_token=HF_TOKEN, device=device)
        except Exception:
            diarizer = None
    return {"model": model, "diarizer": diarizer}


def transcribe(handle, wav_path, lang_code, temperature, model_id):
    import whisperx

    audio = whisperx.load_audio(wav_path)
    result = handle["model"].transcribe(audio, batch_size=4, language=lang_code)

    if handle["diarizer"] is not None:
        try:
            diarize_segments = handle["diarizer"](audio)
            result = whisperx.assign_word_speakers(diarize_segments, result)
        except Exception:
            pass

    segments = []
    texts = []
    for s in result.get("segments", []):
        speaker = s.get("speaker", "SPEAKER_00")
        try:
            speaker_id = int(str(speaker).rsplit("_", 1)[-1])
        except ValueError:
            speaker_id = 0
        segments.append(
            {
                "start": float(s.get("start", 0.0)),
                "end": float(s.get("end", 0.0)),
                "text": s.get("text", "").strip(),
                "speakerId": speaker_id,
            }
        )
        texts.append(s.get("text", "").strip())
    return {
        "text": " ".join(texts),
        "language": language_name(result.get("language"), "Detected"),
        "segments": segments,
    }


app = create_app(
    engine_id="whisperx",
    load=load,
    transcribe=transcribe,
    variant_from_model_id=variant_from_model_id,
    default_variant=DEFAULT_SIZE,
)
