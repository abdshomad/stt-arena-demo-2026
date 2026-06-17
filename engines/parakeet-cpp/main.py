"""parakeet.cpp engine — real GGUF models, downloaded on demand, GPU acceleration."""
import json
import os
import subprocess
import urllib.request

from engine_common import create_app, language_name

MODEL_DIR = os.getenv("PARAKEET_CPP_MODEL_DIR", "/root/.cache/parakeet-cpp")
BIN = os.getenv("PARAKEET_CPP_BIN", "./parakeet-cli")
HF_BASE_URL = "https://huggingface.co/mudler/parakeet-cpp-gguf/resolve/main/{filename}"


def get_gguf_filename(variant: str) -> str:
    v = variant.strip().lower()
    # Map tdt-v3 to the actual file format tdt-0.6b-v3
    if v.startswith("tdt-v3"):
        v = v.replace("tdt-v3", "tdt-0.6b-v3")
    
    # Check if a quantization suffix is already present
    quants = ["-q4_k", "-q5_k", "-q6_k", "-q8_0", "-f16"]
    has_quant = any(v.endswith(q) for q in quants)
    if not has_quant:
        v = v + "-q8_0"
    
    return f"{v}.gguf"


def load(variant: str):
    os.makedirs(MODEL_DIR, exist_ok=True)
    filename = get_gguf_filename(variant)
    model_path = os.path.join(MODEL_DIR, filename)
    if not os.path.exists(model_path):
        tmp_path = model_path + ".part"
        url = HF_BASE_URL.format(filename=filename)
        urllib.request.urlretrieve(url, tmp_path)
        os.rename(tmp_path, model_path)
    return model_path


def variant_from_model_id(model_id: str) -> str:
    # Example model_ids:
    # - parakeet-cpp-ctc-0.6b
    # - parakeet-cpp-rnnt-1.1b
    # - parakeet-cpp-tdt-0.6b-v2
    # - parakeet-cpp-tdt-v3
    # We strip the "parakeet-cpp-" / "parakeet.cpp-" prefix
    variant = model_id.replace("parakeet.cpp", "parakeet-cpp").removeprefix("parakeet-cpp").lstrip("-")
    return variant if variant else "tdt-0.6b-v3"


def transcribe(model_path, wav_path, lang_code, temperature, model_id):
    # Construct parakeet-cli command
    cmd = [BIN, "transcribe", "--model", model_path, "--input", wav_path, "--json", "--threads", str(os.cpu_count() or 4)]
    
    # Determine decoder option based on variant
    if "ctc" in model_path.lower():
        cmd.extend(["--decoder", "ctc"])
    elif "tdt" in model_path.lower():
        cmd.extend(["--decoder", "tdt"])
        
    if lang_code:
        cmd.extend(["--lang", lang_code])
        
    try:
        res = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    except subprocess.CalledProcessError as exc:
        print(f"parakeet-cli failed with exit code {exc.returncode}")
        print(f"STDOUT: {exc.stdout}")
        print(f"STDERR: {exc.stderr}")
        raise RuntimeError(f"parakeet-cli execution failed: {exc.stderr}")
    
    output_json = json.loads(res.stdout)
    text = output_json.get("text", "").strip()
    words = output_json.get("words", [])
    
    segments = []
    if words:
        start = float(words[0].get("start", 0.0))
        end = float(words[-1].get("end", 0.0))
        segments.append(
            {
                "start": start,
                "end": end,
                "text": text,
                "words": [
                    {
                        "word": w.get("w", ""),
                        "start": float(w.get("start", 0.0)),
                        "end": float(w.get("end", 0.0)),
                        "probability": float(w.get("conf", 1.0)),
                    }
                    for w in words
                ],
            }
        )
        
    return {
        "text": text,
        "language": language_name(lang_code, "Detected"),
        "segments": segments,
    }


app = create_app(
    engine_id="parakeet-cpp",
    load=load,
    transcribe=transcribe,
    variant_from_model_id=variant_from_model_id,
    default_variant="tdt-0.6b-v3",
)
