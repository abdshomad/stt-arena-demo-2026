"""'Google AI Edge Eloquent' is fictional. Backed by the real Google edge audio
model: google/gemma-3n-E2B-it (audio understanding via transformers).

Gemma is gated on Hugging Face — requires HF_TOKEN with an accepted license,
otherwise this engine reports N/A.
"""
import os

from engine_common import create_app, torch_device

MODEL_REPO = "google/gemma-3n-E2B-it"


def check():
    if not os.getenv("HF_TOKEN"):
        return False, "google/gemma-3n-E2B-it is gated; set HF_TOKEN (with accepted Gemma license) in .secrets"
    return True, None


def load(variant: str):
    import torch
    from transformers import AutoModelForImageTextToText, AutoProcessor

    token = os.getenv("HF_TOKEN")
    device = torch_device()
    dtype = torch.bfloat16 if device == "cuda" else torch.float32
    processor = AutoProcessor.from_pretrained(MODEL_REPO, token=token)
    model = AutoModelForImageTextToText.from_pretrained(
        MODEL_REPO, torch_dtype=dtype, device_map=device, token=token
    )
    return {"processor": processor, "model": model, "device": device}


def transcribe(handle, wav_path, lang_code, temperature, model_id):
    processor = handle["processor"]
    model = handle["model"]
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "audio", "audio": wav_path},
                {"type": "text", "text": "Transcribe this audio verbatim. Reply with only the transcript."},
            ],
        }
    ]
    inputs = processor.apply_chat_template(
        messages, add_generation_prompt=True, tokenize=True, return_dict=True, return_tensors="pt"
    )
    inputs = inputs.to(handle["device"])
    outputs = model.generate(**inputs, max_new_tokens=500, do_sample=False)
    text = processor.batch_decode(
        outputs[:, inputs["input_ids"].shape[1]:], skip_special_tokens=True
    )[0].strip()
    return {"text": text, "language": None, "segments": []}


app = create_app(
    engine_id="google-ai-edge-eloquent",
    load=load,
    transcribe=transcribe,
    check=check,
)
