# 008 — All 27 engines were whisper-tiny impostors; arena echoed scripted text

## Symptoms
- Every arena battle returned a "transcript" identical (or mock-degraded) to the sample's scripted text regardless of engine choice.
- All engine containers loaded the same model: `whisper.load_model("tiny")` (or its faster-whisper/whisperx/ggml-tiny equivalent), merely labeling responses with the brand name (e.g. "kyutai-stt", "google-gemma-4-audio-understanding").
- The UI battle flow sent `{modelId, text: fullTranscript, ...}` as JSON — no audio — and every engine's JSON branch echoed `text` straight back.

## Root Cause
The demo was built UI-first: engines were scaffolded from a single whisper-tiny template with a JSON echo path so the arena would "work" without real inference. Several engine names (nvidia-nemotron-3.5-asr, microsoft-vibe-voice ASR, mega-asr, srst, inword-ai-stt, nvidia-personaplex, moss-sats, google-omni, google-ai-edge-eloquent, "Gemma 4 audio") have no public model or API at all.

## Resolution
- New shared framework `engines/common/engine_common.py`: multipart-only `/transcribe` (JSON echo removed — HTTP 400), on-demand loading, idle unload, `/health` availability.
- 16 engines now load their genuine models (see `assumptions/002-engine-to-real-model-mapping.md`); 4 map to real hosted APIs gated on keys in `.secrets`; 8 fictional ones report `available:false` and appear gray/N-A in the UI.
- `patch_app.cjs` makes battles send real audio (bundled proklamasi.mp3 or custom uploads) as multipart FormData.
