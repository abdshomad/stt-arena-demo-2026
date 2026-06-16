# 005 — Whisper Size Variants as Battle Entries

Date: 2026-06-12

## User decision
"User can choose which size(s); even can battle between the different size(s)."

## Assumptions / design

1. Sizes are exposed as **separate selectable arena models** (cleanest fit for the existing
   A-vs-B arena UI), not a separate dropdown:
   - `whisper-tiny`, `whisper-base`, `whisper-small`, `whisper-medium`, `whisper-large-v3`, `whisper-large-v3-turbo`
   - `faster-whisper-tiny` … `faster-whisper-large-v3-turbo` (same six)
   - `whisperx-tiny` … `whisperx-large-v3`
   - `whisper-cpp-tiny`, `whisper-cpp-base`, `whisper-cpp-small`, `whisper-cpp-medium`
     (large ggml excluded: ~3GB download + very slow CPU decode adds little demo value)
2. The base ids (`whisper`, `faster-whisper`, `whisperx`, `whisper.cpp`) remain and default to
   **small** (user-confirmed recommended default).
3. Routing: the router strips the size suffix to find the engine container and forwards the
   full `modelId`; the engine derives the size from the id (form field `modelId`), loading that
   variant on demand (LRU, max 2 variants resident per container).
4. The variant entries are injected into `src/data/modelsData.ts` at Docker build time by
   `patch_app.cjs` (submodule itself untouched), with honest metadata (real param counts,
   license MIT/Apache, sourceType unchanged) and WER placeholders marked as estimates.
