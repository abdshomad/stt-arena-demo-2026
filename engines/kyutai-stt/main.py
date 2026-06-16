"""Kyutai STT — real model kyutai/stt-1b-en_fr (transformers port). EN/FR only."""
from engine_common import create_app, torch_device

MODEL_REPO = "kyutai/stt-1b-en_fr-trfs"


def load(variant: str):
    import torch
    from transformers import KyutaiSpeechToTextForConditionalGeneration, KyutaiSpeechToTextProcessor

    device = torch_device()
    dtype = torch.bfloat16 if device == "cuda" else torch.float32
    processor = KyutaiSpeechToTextProcessor.from_pretrained(MODEL_REPO)
    model = KyutaiSpeechToTextForConditionalGeneration.from_pretrained(
        MODEL_REPO, torch_dtype=dtype, device_map=device
    )
    return {"processor": processor, "model": model, "device": device}


def transcribe(handle, wav_path, lang_code, temperature, model_id):
    import librosa

    # Kyutai's mimi codec expects 24 kHz input.
    audio, _sr = librosa.load(wav_path, sr=24000, mono=True)
    inputs = handle["processor"](audio=audio, sampling_rate=24000, return_tensors="pt")
    inputs = inputs.to(handle["device"])
    output_tokens = handle["model"].generate(**inputs)
    text = handle["processor"].batch_decode(output_tokens, skip_special_tokens=True)[0].strip()
    return {"text": text, "language": None, "segments": []}


app = create_app(
    engine_id="kyutai-stt",
    load=load,
    transcribe=transcribe,
)
