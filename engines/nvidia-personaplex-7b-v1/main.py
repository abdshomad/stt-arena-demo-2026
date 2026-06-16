"""NVIDIA PersonaPlex 7B v1 — real local implementation based on Kyutai's Moshi/Mimi."""
import os
import json
import torch
from engine_common import create_app, torch_device

REPO = "nvidia/personaplex-7b-v1"


def check():
    device = torch_device()
    if device != "cuda":
        return False, "NVIDIA PersonaPlex 7B requires a GPU/CUDA environment"
    return True, None


def load(variant: str):
    from transformers import MoshiForConditionalGeneration, MoshiConfig, MimiModel, AutoTokenizer
    from huggingface_hub import hf_hub_download

    token = os.getenv("HF_TOKEN")
    device = torch_device()
    dtype = torch.float32

    # 1. Load config with model_type override to "moshi"
    config_path = hf_hub_download(repo_id=REPO, filename="config.json", token=token)
    with open(config_path) as f:
        config_dict = json.load(f)
    config_dict["model_type"] = "moshi"
    config = MoshiConfig.from_dict(config_dict)

    # 2. Load model
    print("Loading Moshi model...")
    model = MoshiForConditionalGeneration.from_pretrained(
        REPO,
        config=config,
        token=token,
        torch_dtype=dtype,
        device_map="auto" if device == "cuda" else None,
    )

    # 3. Load Mimi model
    print("Loading Mimi codec model...")
    mimi = MimiModel.from_pretrained("kyutai/mimi", token=token)

    # 4. Load Tokenizer
    print("Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(REPO, token=token)

    return {
        "model": model,
        "mimi": mimi,
        "tokenizer": tokenizer,
        "device": device,
    }


def transcribe(handle, wav_path, lang_code, temperature, model_id):
    import librosa
    model = handle["model"]
    mimi = handle["mimi"]
    tokenizer = handle["tokenizer"]

    # Load and resample audio to 24kHz (Mimi expects 24kHz)
    audio, sr = librosa.load(wav_path, sr=24000, mono=True)
    audio_tensor = torch.tensor(audio).unsqueeze(0).unsqueeze(0)  # Shape: [1, 1, seq_len]

    if handle["device"] == "cuda":
        audio_tensor = audio_tensor.cuda()
        mimi = mimi.cuda()

    # Encode audio with Mimi
    with torch.no_grad():
        encoded = mimi.encode(audio_tensor)
        audio_codes = encoded.audio_codes  # Shape: [batch, codebooks, steps]

    # Generate unconditional inputs as template
    inputs = model.get_unconditional_inputs(num_samples=1)
    if handle["device"] == "cuda":
        inputs = {
            k: v.cuda() if isinstance(v, torch.Tensor) else v
            for k, v in inputs.items()
        }

    # Override user_audio_codes in unconditional inputs with the encoded audio codes
    inputs["user_audio_codes"] = audio_codes

    # Ensure input_ids and moshi_audio_codes are aligned with the length of user_audio_codes
    steps = audio_codes.shape[2]
    
    # We pad input_ids and moshi_audio_codes to match steps
    pad_id = tokenizer.pad_token_id if tokenizer.pad_token_id is not None else 0
    inputs["input_ids"] = torch.full((1, steps), pad_id, dtype=torch.long, device=inputs["input_ids"].device)
    
    # moshi_audio_codes shape: [batch, num_codebooks, seq_len]
    inputs["moshi_audio_codes"] = torch.zeros((1, inputs["moshi_audio_codes"].shape[1], steps), dtype=torch.long, device=inputs["moshi_audio_codes"].device)

    # Generate transcript text
    with torch.no_grad():
        output = model.generate(
            **inputs,
            max_new_tokens=256,
            return_audio_waveforms=False,
        )

    # Decode text tokens
    text_tokens = output.sequences[0].tolist()
    text = tokenizer.decode(text_tokens, skip_special_tokens=True).strip()

    return {"text": text, "language": None, "segments": []}


app = create_app(
    engine_id="nvidia-personaplex-7b-v1",
    load=load,
    transcribe=transcribe,
    check=check,
)
