"""Google Gemma 4 Audio Understanding (E2B-it, E4B-it, 12B-it)."""
import os
import torch
from engine_common import create_app, torch_device

VARIANTS = {
    "e2b-it": "google/gemma-4-E2B-it",
    "e4b-it": "google/gemma-4-E4B-it",
    "12b-it": "google/gemma-4-12B-it",
}
DEFAULT_VARIANT = "e2b-it"


def check():
    device = torch_device()
    if device != "cuda":
        return False, "Google Gemma 4 requires a GPU/CUDA environment"
    return True, None


def variant_from_model_id(model_id: str) -> str:
    mid = model_id.lower()
    for v in VARIANTS:
        if v in mid:
            return v
    return DEFAULT_VARIANT


def load(variant: str):
    from transformers import AutoProcessor, AutoModelForMultimodalLM

    repo = VARIANTS.get(variant, VARIANTS[DEFAULT_VARIANT])
    token = os.getenv("HF_TOKEN")
    device = torch_device()
    dtype = torch.bfloat16 if device == "cuda" else torch.float32

    processor = AutoProcessor.from_pretrained(
        repo, token=token, trust_remote_code=True
    )
    model = AutoModelForMultimodalLM.from_pretrained(
        repo,
        torch_dtype=dtype,
        device_map="auto" if device == "cuda" else None,
        trust_remote_code=True,
        token=token,
    )
    return {"processor": processor, "model": model, "device": device}


def transcribe(handle, wav_path, lang_code, temperature, model_id):
    processor = handle["processor"]
    model = handle["model"]

    # Wrap messages using standard format
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Transcribe this audio verbatim. Reply with only the transcript text, nothing else."},
                {"type": "audio", "audio": wav_path},
            ],
        }
    ]
    inputs = processor.apply_chat_template(
        messages,
        tokenize=True,
        return_dict=True,
        return_tensors="pt",
        add_generation_prompt=True,
    )

    if handle["device"] == "cuda":
        inputs = {
            k: v.cuda() if isinstance(v, torch.Tensor) else v
            for k, v in inputs.items()
        }

    # disable thinking mode if possible, or just generate
    generate_kwargs = {
        "max_new_tokens": 1024,
        "temperature": 0.0,
        "do_sample": False,
    }

    with torch.no_grad():
        outputs = model.generate(**inputs, **generate_kwargs)

    prompt_length = inputs["input_ids"].shape[1]
    # Decode only the generated part
    generated_ids = outputs[0][prompt_length:]
    text = processor.decode(generated_ids, skip_special_tokens=True).strip()

    return {"text": text, "language": None, "segments": []}


app = create_app(
    engine_id="google-gemma-4-audio-understanding",
    load=load,
    transcribe=transcribe,
    check=check,
    variant_from_model_id=variant_from_model_id,
    default_variant=DEFAULT_VARIANT,
)
