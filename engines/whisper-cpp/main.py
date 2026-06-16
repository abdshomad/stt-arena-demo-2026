"""whisper.cpp engine — real ggml models, downloaded on demand, size selectable."""
import json
import os
import subprocess
import urllib.request

from engine_common import create_app, language_name

SIZES = {"tiny", "base", "small", "medium"}
DEFAULT_SIZE = "small"
MODEL_DIR = os.getenv("WHISPER_CPP_MODEL_DIR", "/root/.cache/whisper-cpp")
BIN = os.getenv("WHISPER_CPP_BIN", "./whisper-cpp")
GGML_URL = "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-{size}.bin"


def variant_from_model_id(model_id: str) -> str:
    size = model_id.removeprefix("whisper-cpp").removeprefix("whisper.cpp").lstrip("-")
    return size if size in SIZES else DEFAULT_SIZE


def load(variant: str):
    os.makedirs(MODEL_DIR, exist_ok=True)
    model_path = os.path.join(MODEL_DIR, f"ggml-{variant}.bin")
    if not os.path.exists(model_path):
        tmp_path = model_path + ".part"
        urllib.request.urlretrieve(GGML_URL.format(size=variant), tmp_path)
        os.rename(tmp_path, model_path)
    return model_path


def transcribe(model_path, wav_path, lang_code, temperature, model_id):
    cmd = [BIN, "-m", model_path, "-f", wav_path, "-oj", "-t", str(os.cpu_count() or 4)]
    if lang_code:
        cmd.extend(["-l", lang_code])
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    json_path = wav_path + ".json"
    segments = []
    texts = []
    detected = lang_code
    if os.path.exists(json_path):
        with open(json_path) as fh:
            data = json.load(fh)
        detected = data.get("result", {}).get("language", detected)
        for s in data.get("transcription", []):
            offsets = s.get("offsets", {})
            seg_text = s.get("text", "").strip()
            if not seg_text:
                continue
            segments.append(
                {
                    "start": offsets.get("from", 0) / 1000.0,
                    "end": offsets.get("to", 0) / 1000.0,
                    "text": seg_text,
                }
            )
            texts.append(seg_text)
        os.remove(json_path)
    return {
        "text": " ".join(texts),
        "language": language_name(detected, "Detected"),
        "segments": segments,
    }


app = create_app(
    engine_id="whisper.cpp",
    load=load,
    transcribe=transcribe,
    variant_from_model_id=variant_from_model_id,
    default_variant=DEFAULT_SIZE,
)
