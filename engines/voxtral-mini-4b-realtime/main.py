"""Voxtral Mini — real model mistralai/Voxtral-Mini-3B-2507 via transformers.

Note: the arena's marketing name says "4B realtime"; the real released model is 3B
and decidedly not realtime on CPU. Honest latency is reported as measured.
"""
from engine_common import create_app, torch_device

MODEL_REPO = "mistralai/Voxtral-Mini-3B-2507"


def load(variant: str):
    import torch
    from transformers import AutoProcessor, VoxtralForConditionalGeneration

    device = torch_device()
    dtype = torch.bfloat16 if device == "cuda" else torch.float32
    processor = AutoProcessor.from_pretrained(MODEL_REPO)
    model = VoxtralForConditionalGeneration.from_pretrained(
        MODEL_REPO, torch_dtype=dtype, device_map=device
    )
    return {"processor": processor, "model": model, "device": device}


def transcribe(handle, wav_path, lang_code, temperature, model_id):
    processor = handle["processor"]
    model = handle["model"]
    # transformers' API name has a known typo: apply_transcrition_request
    apply_request = getattr(processor, "apply_transcription_request", None) or getattr(
        processor, "apply_transcrition_request"
    )
    inputs = apply_request(language=lang_code or "en", audio=wav_path, model_id=MODEL_REPO)
    inputs = inputs.to(handle["device"])
    outputs = model.generate(**inputs, max_new_tokens=500)
    text = processor.batch_decode(
        outputs[:, inputs.input_ids.shape[1]:], skip_special_tokens=True
    )[0].strip()
    return {"text": text, "language": None, "segments": []}


app = create_app(
    engine_id="voxtral-mini-4b-realtime",
    load=load,
    transcribe=transcribe,
)
