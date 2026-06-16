# 009 — Strict GPU Execution

Date: 2026-06-12

## User decisions
- "Always use GPU (never use CPU, even if it fails)."
- Keep the mapping in `002-engine-to-real-model-mapping.md` (local, API-backed, and N/A) and make sure they are fully and correctly implemented.

## Design
1. **Strict GPU Enforcement**: 
   - We update `torch_device()` in `engines/common/engine_common.py` to raise a `RuntimeError` if CUDA is not available. This prevents silent fallbacks to CPU. Any engine attempting to use CPU will fail immediately, matching the user instruction "never use CPU, even if it fails".
   - For CTranslate2/faster-whisper engines, `device` is set to `"cuda"`. Loading will fail if CUDA is not functional.
2. **GPU support for whisper.cpp**:
   - `whisper-cpp` is rebuilt with CUDA support (`GGML_CUDA=1`) using `nvidia/cuda:12.2.2-devel-ubuntu22.04` as the builder.
   - The runner for `whisper-cpp` is migrated from `python:3.11-slim` to `nvidia/cuda:12.2.2-runtime-ubuntu22.04` to ensure all necessary CUDA runtime libraries (`libcudart.so`, `libcublas.so`, etc.) are present in the container.
   - If CUDA is not available or if the container is run without GPU access, it will fail to load or execute.
3. **GPU Pinning for whisper-cpp**:
   - We pin `whisper-cpp-engine` to GPU 0 in `docker-compose.yml` and `engines/router/main.py`.
