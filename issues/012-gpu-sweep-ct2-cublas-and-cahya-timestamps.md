# 012 — GPU sweep failures: CTranslate2 cublas-12 missing; cahya timestamp config

## Symptoms
After the GPU migration sweep:
- `faster-whisper` and `cahya-faster-whisper-medium-id`: `Library libcublas.so.12 is not found or cannot be loaded`.
- `cahya-whisper-small-id` / `cahya-whisper-medium-id`: `You are trying to return timestamps, but the generation config is not properly set`.

## Root Cause
1. The rebuilt ct2 base pulled the latest PyPI torch, which ships **CUDA 13** nvidia wheels
   (`libcublas.so.13`), while CTranslate2's GPU backend links against **cu12** (`libcublas.so.12`,
   cudnn 9 for cu12).
2. The cahya whisper fine-tunes were published before HF's timestamp-aware generation configs;
   `return_timestamps=True` requires `no_timestamps_token_id` etc. in `generation_config`.

## Resolution
1. `Dockerfile.ct2` additionally installs `nvidia-cublas-cu12` + `nvidia-cudnn-cu12==9.*`
   (different sonames — coexists with torch's cu13 libs); `LD_LIBRARY_PATH` already pointed at
   the right directories.
2. Both cahya engines retry without timestamps when the timestamped call raises, returning a
   single full-text segment.
