"""Shared FastAPI engine server for STT Arena.

Every engine builds its app via create_app(), supplying real load/transcribe
callables. The framework provides:
  - on-demand (lazy) model loading with an LRU of size MAX_LOADED_VARIANTS
  - idle unload after IDLE_UNLOAD_SECONDS without requests
  - /health, /load, /unload endpoints for availability + state
  - multipart-only /transcribe (text-echo JSON mode is intentionally rejected)
  - uniform response schema matching the STT Arena UI
"""

import asyncio
import os
import shutil
import subprocess
import tempfile
import threading
import time
from typing import Callable, Dict, List, Optional, Tuple

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

IDLE_UNLOAD_SECONDS = int(os.getenv("IDLE_UNLOAD_SECONDS", "600"))
MAX_LOADED_VARIANTS = int(os.getenv("MAX_LOADED_VARIANTS", "2"))

LANGUAGE_TO_CODE = {
    "english": "en",
    "indonesian": "id",
    "javanese": "jv",
    "sundanese": "su",
    "french": "fr",
    "german": "de",
    "spanish": "es",
    "japanese": "ja",
    "mandarin": "zh",
    "chinese": "zh",
}
CODE_TO_LANGUAGE = {
    "en": "English",
    "id": "Indonesian",
    "jv": "Javanese",
    "su": "Sundanese",
    "fr": "French",
    "de": "German",
    "es": "Spanish",
    "ja": "Japanese",
    "zh": "Mandarin",
}


def torch_device() -> str:
    """'cuda' when a GPU is visible to this container, else raise RuntimeError."""
    try:
        import torch

        if torch.cuda.is_available():
            return "cuda"
        raise RuntimeError("CUDA is not available inside torch!")
    except Exception as exc:
        raise RuntimeError(f"Strict GPU execution mode: GPU is not available! Details: {exc}")


def free_accelerator_memory() -> None:
    try:
        import gc

        gc.collect()
        import torch

        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    except Exception:
        pass


def language_code(language: Optional[str]) -> Optional[str]:
    if not language:
        return None
    lang = language.strip().lower()
    if lang in LANGUAGE_TO_CODE:
        return LANGUAGE_TO_CODE[lang]
    if len(lang) in (2, 3):
        return lang[:2]
    return None


def language_name(code: Optional[str], fallback: str = "Unknown") -> str:
    if not code:
        return fallback
    return CODE_TO_LANGUAGE.get(code.lower(), code)


def detect_emotion_heuristic(text: str) -> Optional[str]:
    """Keyword heuristic over the real transcript. Honestly labeled as such."""
    if not text:
        return None
    t = text.lower()
    if any(w in t for w in ["happy", "excited", "great", "awesome", "amazing", "senang", "seru", "mantap", "keren"]):
        label = "Excited / Energetic"
    elif any(w in t for w in ["sad", "bad", "fail", "error", "problem", "frustrated", "sedih", "kecewa", "lelah", "masalah"]):
        label = "Frustrated / Concerned"
    elif any(w in t for w in ["what", "how", "why", "where", "when", "?", "apa", "bagaimana", "kenapa", "mengapa"]):
        label = "Inquisitive / Questioning"
    else:
        label = "Neutral / Calm"
    return f"{label} (heuristic)"


def to_wav_16k_mono(src_path: str) -> str:
    """Convert any uploaded audio to 16 kHz mono WAV via ffmpeg."""
    dst_path = src_path + ".16k.wav"
    subprocess.run(
        ["ffmpeg", "-y", "-i", src_path, "-ar", "16000", "-ac", "1", "-f", "wav", dst_path],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return dst_path


class VariantManager:
    """LRU cache of loaded model variants with idle unload."""

    def __init__(self, load: Callable[[str], object], unload: Optional[Callable[[str, object], None]] = None):
        self._load = load
        self._unload = unload
        self._models: Dict[str, object] = {}
        self._last_used: Dict[str, float] = {}
        self._lock = threading.Lock()
        self.loading: Dict[str, bool] = {}
        self._reaper = threading.Thread(target=self._reap_idle, daemon=True)
        self._reaper.start()

    def get(self, variant: str) -> object:
        with self._lock:
            if variant in self._models:
                self._last_used[variant] = time.time()
                return self._models[variant]
            self.loading[variant] = True
        try:
            model = self._load(variant)
        finally:
            self.loading.pop(variant, None)
        with self._lock:
            self._models[variant] = model
            self._last_used[variant] = time.time()
            self._evict_lru_locked()
        return model

    def drop(self, variant: Optional[str] = None) -> List[str]:
        with self._lock:
            victims = [variant] if variant else list(self._models.keys())
            dropped = []
            for v in victims:
                if v in self._models:
                    self._drop_locked(v)
                    dropped.append(v)
        return dropped

    def loaded(self) -> List[str]:
        with self._lock:
            return list(self._models.keys())

    def _drop_locked(self, variant: str) -> None:
        model = self._models.pop(variant, None)
        self._last_used.pop(variant, None)
        if model is not None and self._unload:
            try:
                self._unload(variant, model)
            except Exception:
                pass
        del model
        free_accelerator_memory()

    def _evict_lru_locked(self) -> None:
        while len(self._models) > MAX_LOADED_VARIANTS:
            oldest = min(self._last_used, key=self._last_used.get)
            self._drop_locked(oldest)

    def _reap_idle(self) -> None:
        while True:
            time.sleep(30)
            now = time.time()
            with self._lock:
                for v, ts in list(self._last_used.items()):
                    if now - ts > IDLE_UNLOAD_SECONDS:
                        self._drop_locked(v)


def create_app(
    engine_id: str,
    load: Optional[Callable[[str], object]] = None,
    transcribe: Optional[Callable] = None,
    check: Optional[Callable[[], Tuple[bool, Optional[str]]]] = None,
    variant_from_model_id: Optional[Callable[[str], str]] = None,
    default_variant: str = "default",
    unload: Optional[Callable[[str, object], None]] = None,
    emotion: bool = True,
) -> FastAPI:
    """Build the engine FastAPI app.

    load(variant) -> model handle (heavy imports go inside)
    transcribe(model, wav_path, language_code, temperature, model_id)
        -> {"text": str, "language": str|None, "segments": [...]?}
    check() -> (available, reason); called per request and for /health
    variant_from_model_id(model_id) -> variant key (e.g. whisper size)
    """
    app = FastAPI(title=f"{engine_id} Engine API")
    manager = VariantManager(load, unload) if load else None

    def _availability() -> Tuple[bool, Optional[str]]:
        if check:
            try:
                return check()
            except Exception as exc:  # pragma: no cover
                return False, f"availability check failed: {exc}"
        return True, None

    def _variant(model_id: str) -> str:
        if variant_from_model_id:
            return variant_from_model_id(model_id) or default_variant
        return default_variant

    @app.get("/health")
    async def health():
        available, reason = _availability()
        return {
            "engine": engine_id,
            "available": available,
            "reason": reason,
            "loaded": manager.loaded() if manager else [],
            "loading": bool(manager and manager.loading),
        }

    @app.post("/load")
    async def load_endpoint(request: Request):
        available, reason = _availability()
        if not available:
            return JSONResponse(status_code=503, content={"detail": reason})
        if not manager:
            return {"engine": engine_id, "loaded": [], "note": "stateless engine (no local model)"}
        body = {}
        try:
            body = await request.json()
        except Exception:
            pass
        variant = _variant(body.get("modelId", "") or "")
        await asyncio.to_thread(manager.get, variant)
        return {"engine": engine_id, "loaded": manager.loaded()}

    @app.post("/unload")
    async def unload_endpoint(request: Request):
        if not manager:
            return {"engine": engine_id, "loaded": [], "dropped": []}
        body = {}
        try:
            body = await request.json()
        except Exception:
            pass
        model_id = body.get("modelId") if isinstance(body, dict) else None
        dropped = manager.drop(_variant(model_id) if model_id else None)
        return {"engine": engine_id, "loaded": manager.loaded(), "dropped": dropped}

    @app.post("/transcribe")
    async def transcribe_endpoint(request: Request):
        available, reason = _availability()
        if not available:
            return JSONResponse(
                status_code=503,
                content={"detail": f"{engine_id} unavailable: {reason}", "available": False, "reason": reason},
            )

        content_type = request.headers.get("content-type", "")
        if "multipart/form-data" not in content_type:
            return JSONResponse(
                status_code=400,
                content={"detail": "audio file required (multipart/form-data) — text echo mode removed"},
            )

        form = await request.form()
        file = form.get("file")
        if file is None or isinstance(file, str):
            return JSONResponse(status_code=400, content={"detail": "Missing file field"})

        model_id = str(form.get("modelId") or engine_id)
        language = form.get("language")
        try:
            temperature = float(form.get("temperature", "0.0") or 0.0)
        except ValueError:
            temperature = 0.0
        lang_code = language_code(str(language) if language else None)

        workdir = tempfile.mkdtemp(prefix=f"{engine_id.replace('.', '-')}-")
        src_path = os.path.join(workdir, file.filename or "audio.bin")
        wav_path = None
        start = time.time()
        try:
            with open(src_path, "wb") as fh:
                fh.write(await file.read())
            wav_path = await asyncio.to_thread(to_wav_16k_mono, src_path)

            # Model load + inference are blocking; keep them off the event loop
            # so /health stays responsive while an engine is busy.
            def _load_and_transcribe():
                model = manager.get(_variant(model_id)) if manager else None
                return transcribe(model, wav_path, lang_code, temperature, model_id)

            result = await asyncio.to_thread(_load_and_transcribe)

            text = (result.get("text") or "").strip()
            segments = result.get("segments")
            if not segments:
                segments = [{"start": 0.0, "end": 0.0, "text": text, "speakerId": 0, "words": []}]
            for seg in segments:
                seg.setdefault("speakerId", 0)
                seg.setdefault("words", [])

            latency_ms = int((time.time() - start) * 1000)
            return {
                "text": text,
                "language": result.get("language") or language_name(lang_code, "Detected"),
                "detectedEmotion": detect_emotion_heuristic(text) if emotion else None,
                "mode": "live",
                "latency_ms": latency_ms,
                "model": model_id,
                "segments": segments,
            }
        except subprocess.CalledProcessError:
            return JSONResponse(status_code=400, content={"detail": "ffmpeg could not decode the uploaded audio"})
        except Exception as exc:
            import traceback
            traceback.print_exc()
            return JSONResponse(status_code=500, content={"detail": f"{engine_id} transcription failed: {exc}"})
        finally:
            shutil.rmtree(workdir, ignore_errors=True)

    return app


def create_unavailable_app(engine_id: str, reason: str) -> FastAPI:
    """Engine whose claimed model has no public implementation or API."""
    return create_app(
        engine_id=engine_id,
        load=None,
        transcribe=None,
        check=lambda: (False, reason),
    )
