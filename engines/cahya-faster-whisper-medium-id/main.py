"""Cahya Faster-Whisper Medium ID — cahya/whisper-medium-id converted to CTranslate2.

The conversion runs once at first load and is cached on the shared volume.
"""
import os
import subprocess

from engine_common import create_app, torch_device

MODEL_REPO = "cahya/whisper-medium-id"
CT2_DIR = os.getenv("CT2_DIR", "/root/.cache/ct2/cahya-whisper-medium-id")


def load(variant: str):
    from faster_whisper import WhisperModel

    if not os.path.exists(os.path.join(CT2_DIR, "model.bin")):
        os.makedirs(os.path.dirname(CT2_DIR), exist_ok=True)
        subprocess.run(
            [
                "ct2-transformers-converter",
                "--model", MODEL_REPO,
                "--output_dir", CT2_DIR,
                "--quantization", "int8",
                "--force",
            ],
            check=True,
        )
    device = torch_device()
    compute_type = "float16" if device == "cuda" else "int8"
    return WhisperModel(CT2_DIR, device=device, compute_type=compute_type)


def transcribe(model, wav_path, lang_code, temperature, model_id):
    seg_iter, info = model.transcribe(wav_path, language="id", temperature=temperature)
    segments = []
    texts = []
    for s in seg_iter:
        segments.append({"start": float(s.start), "end": float(s.end), "text": s.text.strip()})
        texts.append(s.text.strip())
    return {"text": " ".join(texts), "language": "Indonesian", "segments": segments}


app = create_app(
    engine_id="cahya-faster-whisper-medium-id",
    load=load,
    transcribe=transcribe,
)
