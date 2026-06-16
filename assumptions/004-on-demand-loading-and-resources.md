# 004 — On-Demand Loading & Resource Strategy (PARTIALLY SUPERSEDED by 008: inference moved to GPU)

Date: 2026-06-12

## User decision
"On-demand loading" (and CPU-friendly, since both L40 GPUs are ~full with other workloads).

## Assumptions / design

1. **Lazy load**: engines start with no model in memory. First `/transcribe` (or explicit
   `POST /load`) loads the model; subsequent requests reuse it.
2. **Idle unload**: a background task unloads the model after `IDLE_UNLOAD_SECONDS` (default
   600s) without requests, freeing RAM. Configurable per engine via env.
3. **CPU inference** for all local engines (`device=cpu`). 503GB host RAM is the budget; the
   heaviest models (voxtral 3B ≈ 12GB fp32, gemma-3n, kyutai 1B) fit comfortably even if several
   are loaded at once, and idle-unload keeps steady-state low.
4. **Shared HuggingFace cache**: all engines mount `./engines/cache` at `/root/.cache` so model
   weights download once and persist across rebuilds/restarts.
5. **First-request latency is accepted**: a cold request may take minutes (download + load).
   `/health` exposes `{available, loaded, loading}` so the UI can show state; the app's 30s
   forward timeout is raised to 600s for live mode (big models on CPU are slow).
6. **Whisper-family multi-size**: one container per engine family holds an LRU cache of up to
   `MAX_LOADED_VARIANTS` (default 2) sizes at a time to bound RAM.
7. The fake "GPU State Manager" page: the router's hardcoded fictional GPUs (H100/A100/4090/T4)
   and LLM list are replaced by real engine state — each STT engine appears as a "model" whose
   loaded/unloaded status comes from live `/health` polls, and load/unload buttons call the
   engine's real `/load`/`/unload`. The "GPU" shown is a single pseudo-device "CPU / system RAM"
   reporting the host's real memory numbers as seen from the container.
