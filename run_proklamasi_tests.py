import os
import sys
import json
import httpx
import difflib
import time

GROUND_TRUTH_PATH = "/home/aiserver/LABS/AI-VOICE/stt-arena-demo-2026/test-proklamasi/teks-proklamasi-ground-truth.txt"
AUDIO_PATH = "/home/aiserver/LABS/AI-VOICE/stt-arena-demo-2026/proklamasi.mp3"
ROUTER_URL = "http://localhost:5000/transcribe"
UNLOAD_URL = "http://localhost:5000/gpus/unload"
OUTPUT_DIR = "/home/aiserver/LABS/AI-VOICE/stt-arena-demo-2026/test-proklamasi"
ERROR_DIR = os.path.join(OUTPUT_DIR, "test-error")

with open(GROUND_TRUTH_PATH, "r") as f:
    ground_truth = f.read().strip()

def normalize(text):
    if not text:
        return ""
    import string
    text = text.lower()
    text = "".join(c for c in text if c not in string.punctuation)
    return " ".join(text.split())

gt_normalized = normalize(ground_truth)
print(f"Ground Truth Normalized: {gt_normalized}\n")

MODELS = [
    "whisper",
    "whisper-large-v3-turbo",
    "faster-whisper",
    "whisperx",
    "whisper-cpp",
    "meta-omnilingual-asr",
    "nvidia-nemotron-3.5-asr",
    "nvidia-nemotron-omni-bf16",
    "nvidia-nemotron-omni-fp8",
    "nvidia-nemotron-omni-nvfp4",
    "nvidia-nemotron-omni",
    "nvidia-parakeet-tdt-v3",
    "google-gemma-4-e2b-it",
    "google-gemma-4-e4b-it",
    "google-gemma-4-12b-it",
    "cahya-whisper-medium-id",
    "cahya-whisper-small-id",
    "cahya-faster-whisper-medium-id",
    "indonesian-nlp-wav2vec2-indonesian-javanese-sundanese",
    "indonesian-nlp-wav2vec2-large-xlsr-indonesian",
    "google-ai-edge-eloquent",
    "moonshine-voice",
    "voxtral-mini-4b-realtime",
    "nvidia-personaplex-7b-v1",
    "nvidia-multitalker-asr",
    "nvidia-nemotron-speech-streaming-en",
    "nvidia-canary-1b-v2",
    "nvidia-canary-180m-flash",
    "nvidia-parakeet-ctc-0.6b",
    "nvidia-parakeet-rnnt-1.1b",
    "kyutai-stt",
    "nvidia-parakeet-tdt-0.6b-v2",
    "parakeet-cpp-ctc-0.6b",
    "parakeet-cpp-rnnt-1.1b",
    "parakeet-cpp-tdt-0.6b-v2",
    "parakeet-cpp-tdt-v3",
    "nvidia-canary-1b-flash",
    "kyutai-stt-2.6b-en",
    "funasr-sensevoice",
    "funasr-paraformer-zh",
    "funasr-paraformer-en"
]

results = {}

selected_models = sys.argv[1:] if len(sys.argv) > 1 else MODELS

for model in selected_models:
    if model not in MODELS:
        print(f"Warning: Model {model} is not in the predefined MODELS list.")
    print(f"Testing model: {model} ...")
    try:
        with open(AUDIO_PATH, "rb") as f:
            audio_bytes = f.read()

        response = httpx.post(
            ROUTER_URL,
            data={
                "modelId": model,
                "language": "Indonesian"
            },
            files={"file": ("proklamasi.mp3", audio_bytes, "audio/mpeg")},
            timeout=300.0
        )
        
        status_code = response.status_code
        try:
            resp_json = response.json()
        except Exception:
            resp_json = {"detail": response.text}

        if status_code == 200 and "text" in resp_json:
            text = resp_json["text"]
            text_normalized = normalize(text)
            ratio = difflib.SequenceMatcher(None, gt_normalized, text_normalized).ratio()
            print(f"  Result: {text[:100]}...")
            print(f"  Similarity Ratio: {ratio:.3f}")
            results[model] = {
                "success": True,
                "text": text,
                "ratio": ratio
            }
            output_file = os.path.join(OUTPUT_DIR, f"{model}-result.txt")
            with open(output_file, "w") as out_f:
                out_f.write(text + "\n")
        else:
            detail = resp_json.get("detail", str(resp_json))
            print(f"  Error {status_code}: {detail}")
            results[model] = {
                "success": False,
                "error": detail
            }
            os.makedirs(ERROR_DIR, exist_ok=True)
            output_file = os.path.join(ERROR_DIR, f"{model}-result.txt")
            with open(output_file, "w") as out_f:
                out_f.write(f"Error: {detail}\n")
    except Exception as e:
        print(f"  Exception: {e}")
        results[model] = {
            "success": False,
            "error": str(e)
        }
        os.makedirs(ERROR_DIR, exist_ok=True)
        output_file = os.path.join(ERROR_DIR, f"{model}-result.txt")
        with open(output_file, "w") as out_f:
            out_f.write(f"Error: {e}\n")
    finally:
        # Unload the model to free GPU VRAM
        print(f"  Unloading model: {model} ...")
        try:
            unload_resp = httpx.post(UNLOAD_URL, json={"modelId": model}, timeout=30.0)
            if unload_resp.status_code == 200:
                print("  Unloaded successfully.")
            else:
                print(f"  Unload failed: {unload_resp.status_code}")
        except Exception as ue:
            print(f"  Unload exception: {ue}")
        time.sleep(2.0)

print("\n=== SUMMARY ===")
for model, res in results.items():
    if res["success"]:
        print(f"{model}: Success (Ratio: {res['ratio']:.3f})")
    else:
        print(f"{model}: Failed ({res['error'][:80]})")
