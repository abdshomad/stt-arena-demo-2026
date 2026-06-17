"""NVIDIA Nemotron 3 Nano Omni — real models in BF16, FP8, and NVFP4 precisions."""
import os
import torch
from engine_common import create_app, torch_device

VARIANTS = {
    "bf16": "nvidia/Nemotron-3-Nano-Omni-30B-A3B-Reasoning-BF16",
    "fp8": "nvidia/Nemotron-3-Nano-Omni-30B-A3B-Reasoning-FP8",
    "nvfp4": "nvidia/Nemotron-3-Nano-Omni-30B-A3B-Reasoning-NVFP4",
}
DEFAULT_VARIANT = "bf16"


def check():
    device = torch_device()
    if device != "cuda":
        return False, "NVIDIA Nemotron 3 Nano Omni (30B) requires a GPU/CUDA environment"
    return True, None


def variant_from_model_id(model_id: str) -> str:
    for v in VARIANTS:
        if v in model_id.lower():
            return v
    return DEFAULT_VARIANT


def load(variant: str):
    from transformers import AutoModel, AutoProcessor

    repo = VARIANTS.get(variant, VARIANTS[DEFAULT_VARIANT])
    token = os.getenv("HF_TOKEN")
    device = torch_device()
    dtype = torch.bfloat16 if device == "cuda" else torch.float32

    processor = AutoProcessor.from_pretrained(
        repo, token=token, trust_remote_code=True
    )
    model = AutoModel.from_pretrained(
        repo,
        torch_dtype=dtype,
        device_map="auto" if device == "cuda" else None,
        trust_remote_code=True,
        token=token,
        attn_implementation="eager",
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
                {"type": "audio", "audio": wav_path},
                {
                    "type": "text",
                    "text": "Transcribe this audio verbatim. Reply with only the transcript text, nothing else.",
                },
            ],
        }
    ]
    prompt = processor.apply_chat_template(messages, add_generation_prompt=True)
    inputs = processor(text=prompt, audio=wav_path, return_tensors="pt")

    if handle["device"] == "cuda":
        inputs = {
            k: v.cuda() if isinstance(v, torch.Tensor) else v
            for k, v in inputs.items()
        }

    # Disable thinking mode for transcription as recommended for STT
    generate_kwargs = {
        "max_new_tokens": 1024,
        "temperature": 0.0,
        "do_sample": False,
        "chat_template_kwargs": {"enable_thinking": False},
    }

    with torch.no_grad():
        outputs = model.generate(**inputs, **generate_kwargs)

    prompt_length = inputs["input_ids"].shape[1]
    text = processor.batch_decode(
        outputs[:, prompt_length:], skip_special_tokens=True
    )[0].strip()

    return {"text": text, "language": None, "segments": []}


app = create_app(
    engine_id="nvidia-nemotron-omni",
    load=load,
    transcribe=transcribe,
    check=check,
    variant_from_model_id=variant_from_model_id,
    default_variant=DEFAULT_VARIANT,
)

