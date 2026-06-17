"""STT Arena Router Gateway.

- POST /transcribe       : dispatch multipart audio to the right engine by modelId
                           (whisper size variants like `whisper-large-v3` resolve
                           to their engine family container)
- GET  /engines/health   : aggregate every engine's /health (for UI availability)
- GET  /gpus (+load/...) : real resource page — one pseudo-device backed by actual
                           host RAM numbers, model load state read live from the
                           engines; load/unload proxy to the engines' real
                           /load and /unload endpoints.
"""

import asyncio
import logging
import os
import time
from typing import Dict, Optional

import httpx
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("router")

app = FastAPI(title="STT Arena Router Gateway")

# engine key -> (base url, human name, approx resident size GB when loaded, params, group)
ENGINES: Dict[str, dict] = {
    "whisper": {"url": "http://whisper-engine:8001", "name": "OpenAI Whisper", "sizeGb": 1.0, "parameters": "39M-1.5B", "local": True},
    "faster-whisper": {"url": "http://faster-whisper-engine:8002", "name": "Faster-Whisper (CTranslate2)", "sizeGb": 0.6, "parameters": "39M-1.5B", "local": True},
    "whisperx": {"url": "http://whisperx-engine:8003", "name": "WhisperX", "sizeGb": 0.8, "parameters": "39M-1.5B", "local": True},
    "whisper-cpp": {"url": "http://whisper-cpp-engine:8004", "name": "whisper.cpp (ggml)", "sizeGb": 0.5, "parameters": "39M-769M", "local": True},
    "meta-omnilingual-asr": {"url": "http://meta-omnilingual-engine:8005", "name": "Meta Omnilingual ASR (CTC 300M)", "sizeGb": 1.2, "parameters": "300M", "local": True},
    "microsoft-vibe-voice-asr": {"url": "http://microsoft-vibe-voice-engine:8006", "name": "Azure Speech (VibeVoice N/A)", "sizeGb": 0.0, "parameters": "API", "local": False},
    "nvidia-nemotron-3.5-asr": {"url": "http://nvidia-nemotron-3.5-asr-engine:8007", "name": "NVIDIA Nemotron 3.5 ASR", "sizeGb": 2.5, "parameters": "600M", "local": True},
    "nvidia-nemotron-omni-bf16": {"url": "http://nvidia-nemotron-omni-engine:8008", "name": "NVIDIA Nemotron 3 Nano Omni BF16", "sizeGb": 60.0, "parameters": "30B", "local": True},
    "nvidia-nemotron-omni-fp8": {"url": "http://nvidia-nemotron-omni-engine:8008", "name": "NVIDIA Nemotron 3 Nano Omni FP8", "sizeGb": 30.0, "parameters": "30B", "local": True},
    "nvidia-nemotron-omni-nvfp4": {"url": "http://nvidia-nemotron-omni-engine:8008", "name": "NVIDIA Nemotron 3 Nano Omni NVFP4", "sizeGb": 15.0, "parameters": "30B", "local": True},
    "nvidia-nemotron-omni": {"url": "http://nvidia-nemotron-omni-engine:8008", "name": "NVIDIA Nemotron 3 Nano Omni (Default)", "sizeGb": 60.0, "parameters": "30B", "local": True},
    "mega-asr": {"url": "http://mega-asr-engine:8009", "name": "Mega-ASR (N/A)", "sizeGb": 0.0, "parameters": "N/A", "local": False},
    "nvidia-parakeet-tdt-v3": {"url": "http://nvidia-parakeet-tdt-v3-engine:8010", "name": "NVIDIA Parakeet TDT 0.6B v3", "sizeGb": 2.5, "parameters": "600M", "local": True},
    "google-gemma-4-e2b-it": {"url": "http://google-gemma-4-audio-understanding-engine:8011", "name": "Google Gemma 4 E2B Instruct", "sizeGb": 5.0, "parameters": "2B", "local": True},
    "google-gemma-4-e4b-it": {"url": "http://google-gemma-4-audio-understanding-engine:8011", "name": "Google Gemma 4 E4B Instruct", "sizeGb": 10.0, "parameters": "4B", "local": True},
    "google-gemma-4-12b-it": {"url": "http://google-gemma-4-audio-understanding-engine:8011", "name": "Google Gemma 4 12B Instruct", "sizeGb": 25.0, "parameters": "12B", "local": True},
    "cahya-whisper-medium-id": {"url": "http://cahya-whisper-medium-id-engine:8012", "name": "Cahya Whisper Medium ID", "sizeGb": 3.1, "parameters": "769M", "local": True},
    "cahya-whisper-small-id": {"url": "http://cahya-whisper-small-id-engine:8013", "name": "Cahya Whisper Small ID", "sizeGb": 1.0, "parameters": "244M", "local": True},
    "cahya-faster-whisper-medium-id": {"url": "http://cahya-faster-whisper-medium-id-engine:8014", "name": "Cahya Faster-Whisper Medium ID (int8)", "sizeGb": 0.8, "parameters": "769M", "local": True},
    "indonesian-nlp-wav2vec2-indonesian-javanese-sundanese": {"url": "http://indonesian-nlp-wav2vec2-indonesian-javanese-sundanese-engine:8015", "name": "Wav2Vec2 ID/JV/SU", "sizeGb": 1.3, "parameters": "300M", "local": True},
    "indonesian-nlp-wav2vec2-large-xlsr-indonesian": {"url": "http://indonesian-nlp-wav2vec2-large-xlsr-indonesian-engine:8016", "name": "Wav2Vec2 XLSR Indonesian", "sizeGb": 1.3, "parameters": "300M", "local": True},
    "google-ai-edge-eloquent": {"url": "http://google-ai-edge-eloquent-engine:8017", "name": "Gemma 3n E2B Audio (Eloquent N/A)", "sizeGb": 6.0, "parameters": "2B effective", "local": True},
    "google-omni": {"url": "http://google-omni-engine:8018", "name": "Gemini API (Google Omni N/A)", "sizeGb": 0.0, "parameters": "API", "local": False},
    "inword-ai-stt": {"url": "http://inword-ai-stt-engine:8019", "name": "Inword AI STT (N/A)", "sizeGb": 0.0, "parameters": "N/A", "local": False},
    "gpt-realtime-whisper": {"url": "http://gpt-realtime-whisper-engine:8020", "name": "OpenAI Transcribe API", "sizeGb": 0.0, "parameters": "API", "local": False},
    "moonshine-voice": {"url": "http://moonshine-voice-engine:8021", "name": "Moonshine Base", "sizeGb": 0.5, "parameters": "61M", "local": True},
    "voxtral-mini-4b-realtime": {"url": "http://voxtral-mini-4b-realtime-engine:8022", "name": "Voxtral Mini 3B", "sizeGb": 13.0, "parameters": "3B", "local": True},
    "nvidia-personaplex-7b-v1": {"url": "http://nvidia-personaplex-7b-v1-engine:8023", "name": "NVIDIA PersonaPlex 7B v1", "sizeGb": 15.0, "parameters": "7B", "local": True},
    "moss-sats-asr-with-diarization": {"url": "http://moss-sats-asr-with-diarization-engine:8024", "name": "MOSS SATS ASR (N/A)", "sizeGb": 0.0, "parameters": "N/A", "local": False},
    "srst": {"url": "http://srst-engine:8025", "name": "SRST (N/A)", "sizeGb": 0.0, "parameters": "N/A", "local": False},
    "nvidia-multitalker-asr": {"url": "http://nvidia-multitalker-asr-engine:8026", "name": "NVIDIA MultiTalker ASR", "sizeGb": 2.5, "parameters": "600M", "local": True},
    "nvidia-nemotron-speech-streaming-en": {"url": "http://nvidia-nemotron-speech-streaming-en-engine:8031", "name": "NVIDIA Nemotron Speech Streaming 0.6B", "sizeGb": 2.5, "parameters": "600M", "local": True},
    "nvidia-canary-1b-v2": {"url": "http://nvidia-canary-1b-v2-engine:8032", "name": "NVIDIA Canary 1B v2", "sizeGb": 4.0, "parameters": "1B", "local": True},
    "nvidia-canary-180m-flash": {"url": "http://nvidia-canary-180m-flash-engine:8033", "name": "NVIDIA Canary 180M Flash", "sizeGb": 0.8, "parameters": "180M", "local": True},
    "nvidia-parakeet-ctc-0.6b": {"url": "http://nvidia-parakeet-ctc-0.6b-engine:8034", "name": "NVIDIA Parakeet CTC 0.6B", "sizeGb": 2.5, "parameters": "600M", "local": True},
    "nvidia-parakeet-rnnt-1.1b": {"url": "http://nvidia-parakeet-rnnt-1.1b-engine:8035", "name": "NVIDIA Parakeet RNNT 1.1B", "sizeGb": 4.5, "parameters": "1.1B", "local": True},
    "kyutai-stt": {"url": "http://kyutai-stt-engine:8027", "name": "Kyutai STT 1B (EN/FR)", "sizeGb": 4.0, "parameters": "1B", "local": True},
    "nvidia-parakeet-tdt-0.6b-v2": {"url": "http://nvidia-parakeet-tdt-0.6b-v2-engine:8036", "name": "NVIDIA Parakeet TDT 0.6B v2", "sizeGb": 2.5, "parameters": "600M", "local": True},
    "parakeet-cpp-ctc-0.6b": {"url": "http://parakeet-cpp-engine:8041", "name": "parakeet.cpp CTC 0.6B", "sizeGb": 0.7, "parameters": "600M", "local": True},
    "parakeet-cpp-rnnt-1.1b": {"url": "http://parakeet-cpp-engine:8041", "name": "parakeet.cpp RNNT 1.1B", "sizeGb": 1.2, "parameters": "1.1B", "local": True},
    "parakeet-cpp-tdt-0.6b-v2": {"url": "http://parakeet-cpp-engine:8041", "name": "parakeet.cpp TDT 0.6B v2", "sizeGb": 0.7, "parameters": "600M", "local": True},
    "parakeet-cpp-tdt-v3": {"url": "http://parakeet-cpp-engine:8041", "name": "parakeet.cpp TDT 0.6B v3", "sizeGb": 0.7, "parameters": "600M", "local": True},
    "nvidia-canary-1b-flash": {"url": "http://nvidia-canary-1b-flash-engine:8037", "name": "NVIDIA Canary 1B Flash", "sizeGb": 4.0, "parameters": "1B", "local": True},
    "kyutai-stt-2.6b-en": {"url": "http://kyutai-stt-2.6b-en-engine:8038", "name": "Kyutai STT 2.6B (EN)", "sizeGb": 10.0, "parameters": "2.6B", "local": True},
    "funasr-sensevoice": {"url": "http://funasr-engine:8040", "name": "FunASR SenseVoiceSmall", "sizeGb": 0.5, "parameters": "80M", "local": True},
    "funasr-paraformer-zh": {"url": "http://funasr-engine:8040", "name": "FunASR Paraformer Chinese", "sizeGb": 0.9, "parameters": "220M", "local": True},
    "funasr-paraformer-en": {"url": "http://funasr-engine:8040", "name": "FunASR Paraformer English", "sizeGb": 0.9, "parameters": "220M", "local": True},
    "browser-web-speech-api": {"url": "http://localhost", "name": "Web Speech API (Browser Native)", "sizeGb": 0.0, "parameters": "N/A", "local": False},
    "browser-transformers-js": {"url": "http://localhost", "name": "Transformers.js (Whisper Tiny)", "sizeGb": 0.0, "parameters": "75M", "local": False},
    "browser-whisper-cpp-tiny-en": {"url": "http://localhost", "name": "whisper.cpp (Tiny EN)", "sizeGb": 0.0, "parameters": "75M", "local": False},
    "browser-whisper-cpp-base-en": {"url": "http://localhost", "name": "whisper.cpp (Base EN)", "sizeGb": 0.0, "parameters": "142M", "local": False},
    "browser-whisper-cpp-base": {"url": "http://localhost", "name": "whisper.cpp (Base Multilingual)", "sizeGb": 0.0, "parameters": "142M", "local": False},
    "browser-whisper-cpp-tiny-en-q5_1": {"url": "http://localhost", "name": "whisper.cpp (Tiny EN Q5_1)", "sizeGb": 0.0, "parameters": "31M", "local": False},
    "browser-whisper-cpp-base-en-q5_1": {"url": "http://localhost", "name": "whisper.cpp (Base EN Q5_1)", "sizeGb": 0.0, "parameters": "57M", "local": False},
    "browser-mozilla-deepspeech": {"url": "http://localhost", "name": "Mozilla DeepSpeech (Browser)", "sizeGb": 0.0, "parameters": "188M", "local": False},
    "browser-baidu-deepspeech": {"url": "http://localhost", "name": "Baidu DeepSpeech (Browser)", "sizeGb": 0.0, "parameters": "210M", "local": False},
    "browser-vosk": {"url": "http://localhost", "name": "Vosk (Browser)", "sizeGb": 0.0, "parameters": "45M", "local": False},
    "browser-picovoice": {"url": "http://localhost", "name": "Picovoice Cheetah (Browser)", "sizeGb": 0.0, "parameters": "15M", "local": False},
}

def resolve_engine(model_id: str) -> Optional[str]:
    mid = (model_id or "").strip().replace("whisper.cpp", "whisper-cpp")
    if mid in ENGINES:
        return mid
    # Size variants, e.g. whisper-large-v3, faster-whisper-tiny, whisper-cpp-small,
    # whisperx-medium — longest engine key prefix wins.
    candidates = [k for k in ENGINES if mid.startswith(k + "-")]
    if candidates:
        return max(candidates, key=len)
    return None


HEALTH_CACHE: dict = {"ts": 0.0, "data": None}
HEALTH_TTL_SECONDS = 5


async def fetch_health() -> dict:
    now = time.time()
    if HEALTH_CACHE["data"] is not None and now - HEALTH_CACHE["ts"] < HEALTH_TTL_SECONDS:
        return HEALTH_CACHE["data"]

    async def one(key: str, info: dict):
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                resp = await client.get(f"{info['url']}/health")
                resp.raise_for_status()
                return key, resp.json()
        except Exception as exc:
            return key, {"engine": key, "available": False, "reason": f"engine unreachable: {type(exc).__name__}", "loaded": [], "loading": False}

    results = await asyncio.gather(*(one(k, v) for k, v in ENGINES.items()))
    data = {k: payload for k, payload in results}
    HEALTH_CACHE["ts"] = now
    HEALTH_CACHE["data"] = data
    return data


@app.get("/engines/health")
async def engines_health():
    data = await fetch_health()
    return {"engines": data, "ts": int(time.time())}


# Which physical GPU each local engine is pinned to (CUDA_VISIBLE_DEVICES in
# docker-compose.yml). whisper-cpp runs on CPU by design; API/N-A engines none.
GPU_PIN = {
    "whisper": 0, "faster-whisper": 0, "whisperx": 0,
    "whisper-cpp": 0,
    "cahya-whisper-medium-id": 0, "cahya-whisper-small-id": 0,
    "cahya-faster-whisper-medium-id": 0,
    "indonesian-nlp-wav2vec2-indonesian-javanese-sundanese": 0,
    "indonesian-nlp-wav2vec2-large-xlsr-indonesian": 0,
    "moonshine-voice": 0,
    "nvidia-parakeet-tdt-v3": 1, "kyutai-stt": 1,
    "voxtral-mini-4b-realtime": 1, "google-ai-edge-eloquent": 1,
    "google-gemma-4-e2b-it": 1, "google-gemma-4-e4b-it": 1, "google-gemma-4-12b-it": 1,
    "nvidia-personaplex-7b-v1": 1,
    "meta-omnilingual-asr": 1,
    "nvidia-nemotron-3.5-asr": 1,
    "nvidia-multitalker-asr": 1,
    "nvidia-nemotron-speech-streaming-en": 0,
    "nvidia-canary-1b-v2": 0,
    "nvidia-canary-180m-flash": 0,
    "nvidia-parakeet-ctc-0.6b": 0,
    "nvidia-parakeet-rnnt-1.1b": 1,
    "nvidia-parakeet-tdt-0.6b-v2": 0,
    "parakeet-cpp-ctc-0.6b": 0,
    "parakeet-cpp-rnnt-1.1b": 0,
    "parakeet-cpp-tdt-0.6b-v2": 0,
    "parakeet-cpp-tdt-v3": 0,
    "nvidia-canary-1b-flash": 0,
    "kyutai-stt-2.6b-en": 1,
    "funasr-sensevoice": 0,
    "funasr-paraformer-zh": 0,
    "funasr-paraformer-en": 0,
    "nvidia-nemotron-omni-bf16": 0,
    "nvidia-nemotron-omni-fp8": 0,
    "nvidia-nemotron-omni-nvfp4": 0,
    "nvidia-nemotron-omni": 0,
}


def read_real_gpus() -> list:
    """Real GPU stats via nvidia-smi (router runs with gpus: all)."""
    import subprocess

    try:
        out = subprocess.run(
            ["nvidia-smi",
             "--query-gpu=index,name,memory.total,memory.used,utilization.gpu,temperature.gpu,power.draw,power.limit",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=5, check=True,
        ).stdout
    except Exception:
        return []
    gpus = []
    for line in out.strip().splitlines():
        idx, name, mem_total, mem_used, util, temp, pwr, pwr_lim = [x.strip() for x in line.split(",")]
        gpus.append({
            "id": f"gpu-{idx}",
            "name": f"{name} (real)",
            "vramTotalGb": round(float(mem_total) / 1024, 1),
            "vramUsedGb": round(float(mem_used) / 1024, 1),
            "utilization": int(float(util)),
            "temperature": int(float(temp)),
            "powerUsageW": int(float(pwr)),
            "powerLimitW": int(float(pwr_lim)),
            "loadedModelIds": [],
        })
    return gpus


def read_meminfo_gb() -> dict:
    info = {}
    try:
        with open("/proc/meminfo") as fh:
            for line in fh:
                parts = line.split()
                if parts[0].rstrip(":") in ("MemTotal", "MemAvailable"):
                    info[parts[0].rstrip(":")] = int(parts[1]) / 1024 / 1024
    except Exception:
        pass
    return info


async def gpu_state() -> dict:
    health = await fetch_health()

    devices = read_real_gpus()
    if not devices:  # no GPU visible: fall back to a real RAM pseudo-device
        mem = read_meminfo_gb()
        total_gb = round(mem.get("MemTotal", 0.0), 1)
        used_gb = round(total_gb - mem.get("MemAvailable", 0.0), 1)
        devices = [{
            "id": "cpu-0",
            "name": "Host CPU / System RAM (real)",
            "vramTotalGb": total_gb,
            "vramUsedGb": used_gb,
            "utilization": int(min(99, (used_gb / total_gb) * 100)) if total_gb else 0,
            "temperature": 0,
            "powerUsageW": 0,
            "powerLimitW": 0,
            "loadedModelIds": [],
        }]
    device_ids = [d["id"] for d in devices]

    models = []
    for key, info in ENGINES.items():
        h = health.get(key, {})
        loaded = bool(h.get("loaded"))
        if key.startswith("browser-"):
            status = "loaded" if key == "browser-web-speech-api" else "unloaded"
            description = "Runs directly in user's browser client-side"
            format_val = "Browser Native" if key == "browser-web-speech-api" else "Browser WASM"
            capabilities = ["ASR / STT", "Multilingual Capabilities"] if key in ["browser-web-speech-api", "browser-transformers-js", "browser-whisper-cpp-base", "browser-vosk", "browser-picovoice"] else ["ASR / STT"]
        else:
            if not info["local"]:
                status = "unloaded"
                description = "Remote API or N/A — no local weights"
            else:
                status = "loading" if h.get("loading") else ("loaded" if loaded else "unloaded")
                description = "Real local model, loaded on demand (GPU)"
            if not h.get("available", False) and not loaded:
                description = h.get("reason") or description
            format_val = "GPU / on-demand" if info["local"] else "API"
            capabilities = ["ASR / STT"]

        entry = {
            "id": key,
            "name": info["name"],
            "sizeGb": info["sizeGb"],
            "parameters": info["parameters"],
            "format": format_val,
            "capabilities": capabilities,
            "description": description,
            "status": status,
        }
        if status == "loaded" and not key.startswith("browser-"):
            pin = GPU_PIN.get(key)
            gpu_id = f"gpu-{pin}" if pin is not None and f"gpu-{pin}" in device_ids else device_ids[0]
            entry["gpuId"] = gpu_id
            next(d for d in devices if d["id"] == gpu_id)["loadedModelIds"].append(key)
        models.append(entry)

    return {"gpus": devices, "models": models, "mode": "live"}


@app.get("/gpus")
async def get_gpus():
    return await gpu_state()


@app.post("/gpus/load")
async def gpus_load(request: Request):
    data = await request.json()
    key = resolve_engine(data.get("modelId", ""))
    if not key:
        raise HTTPException(status_code=404, detail="Unknown model")
    try:
        async with httpx.AsyncClient(timeout=1800.0) as client:
            resp = await client.post(f"{ENGINES[key]['url']}/load", json={"modelId": data.get("modelId")})
            resp.raise_for_status()
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"engine load failed: {exc}")
    HEALTH_CACHE["data"] = None
    return await gpu_state()


@app.post("/gpus/unload")
async def gpus_unload(request: Request):
    data = await request.json()
    key = resolve_engine(data.get("modelId", ""))
    if not key:
        raise HTTPException(status_code=404, detail="Unknown model")
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(f"{ENGINES[key]['url']}/unload", json={})
            resp.raise_for_status()
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"engine unload failed: {exc}")
    HEALTH_CACHE["data"] = None
    return await gpu_state()


@app.post("/gpus/move")
async def gpus_move(request: Request):
    # Single real device — moving between GPUs is not applicable.
    return await gpu_state()


@app.post("/transcribe/{model_path:path}")
async def transcribe_by_path(
    model_path: str,
    file: UploadFile = File(...),
    language: Optional[str] = Form(None),
    isMumbled: Optional[str] = Form("false"),
    temperature: Optional[str] = Form("0.2"),
    maxTokens: Optional[str] = Form("500"),
    vocabBoost: Optional[str] = Form(None),
):
    return await transcribe(
        file=file,
        modelId=model_path,
        language=language,
        isMumbled=isMumbled,
        temperature=temperature,
        maxTokens=maxTokens,
        vocabBoost=vocabBoost,
    )


@app.post("/transcribe")
async def transcribe(
    file: UploadFile = File(...),
    modelId: str = Form("faster-whisper"),
    language: Optional[str] = Form(None),
    isMumbled: Optional[str] = Form("false"),
    temperature: Optional[str] = Form("0.2"),
    maxTokens: Optional[str] = Form("500"),
    vocabBoost: Optional[str] = Form(None),
):
    key = resolve_engine(modelId)
    if not key:
        return JSONResponse(status_code=404, content={"detail": f"Unknown modelId '{modelId}'"})
    target_url = f"{ENGINES[key]['url']}/transcribe"
    logger.info("Routing model '%s' -> %s", modelId, target_url)

    content = await file.read()
    data = {
        "modelId": modelId,
        "isMumbled": isMumbled or "false",
        "temperature": temperature or "0.2",
        "maxTokens": maxTokens or "500",
    }
    if language:
        data["language"] = language
    if vocabBoost:
        data["vocabBoost"] = vocabBoost

    timeout = float(os.getenv("ENGINE_TIMEOUT_SECONDS", "1800"))
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(
                target_url,
                data=data,
                files={"file": (file.filename or "audio.bin", content, file.content_type or "application/octet-stream")},
            )
    except httpx.HTTPError as exc:
        return JSONResponse(status_code=502, content={"detail": f"engine '{key}' unreachable: {exc}"})

    return JSONResponse(status_code=resp.status_code, content=resp.json())
