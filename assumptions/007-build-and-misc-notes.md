# 007 — Build & Miscellaneous Notes

Date: 2026-06-12

1. **Shared base images**: engine images derive from `stt-arena-base:{api,whisper,ct2,whisperx,transformers,nemo,omnilingual}`, built once via `./engines/build-bases.sh` (documented in README). docker-compose build contexts changed to `./engines` so engines can COPY the shared `common/engine_common.py`.
2. **CUDA wheels on a CPU box**: whisperx/nemo/omnilingual pull CUDA-enabled torch through their own dependency pins (images ~6-9GB). They run fine on CPU; disk is ample. Not worth fighting pip resolution for now.
3. **Whisper-family default size**: bare ids (`whisper`, `faster-whisper`, `whisperx`, `whisper.cpp`) default to `small` per user's "small (Recommended)"-adjacent answer ("user can choose" — the choice is the size-variant entries; the default stays small).
4. **`custom-mic` sample stays simulated**: the app's mic flow never captures a real recording (no MediaRecorder in the submodule). Custom *file/URL uploads* and the bundled proklamasi.mp3 are the real-audio paths. Adding true mic capture means substantial new submodule code — deferred unless requested.
5. **Scripted samples & dialogue profiles** remain text-only; in live mode they hit the JSON path, the router/engines reject text-only requests, and the server's clearly-flagged mock fallback (with `fallbackWarning`) answers. The UI surfaces that warning.
6. **WER/latency metadata for the new size-variant entries are estimates** (typical published whisper benchmark ranges), used only for the static leaderboard display, not for live battle results.
7. **proklamasi.mp3 reference transcript** uses the official proclamation wording (period spelling "boelan/tahoen" as spoken in the recording).
8. **.secrets keys the user can add later**: `OPENAI_API_KEY`, `GEMINI_API_KEY`, `AZURE_SPEECH_KEY`, `AZURE_SPEECH_REGION`, `HF_TOKEN` (for gated Gemma 3n + whisperx pyannote diarization). Engines pick them up on restart; UI un-grays automatically via /api/engines/health polling.
