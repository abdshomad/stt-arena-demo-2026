# 008 — GPU Migration (supersedes the CPU parts of 004)

Date: 2026-06-12

## User decisions
- "all inference should use GPU instead of CPU; use available GPU"
- Asked which GPU processes to free: user chose **all of them** (both vLLM servers,
  all `ocr-engine-*`, all `ocr-pipeline-*`, `paddleocr-pipeline-api`). They were stopped with
  `docker stop` (not removed — restartable with `docker start`). RustDesk (host remote desktop,
  0.5GB) was left running.

## Design
1. Base images rebuilt with default PyPI (CUDA) torch in a single pip resolve — this also fixed
   the `torchvision::nms` mismatch that broke transformers pipelines (issue 011).
2. All engine services get `gpus: all`; engines are pinned via `CUDA_VISIBLE_DEVICES`:
   - **GPU 0**: whisper, faster-whisper, whisperx, cahya ×3, wav2vec2 ×2, moonshine
   - **GPU 1**: parakeet, kyutai, voxtral, gemma-3n (eloquent), meta-omnilingual (heavy models)
3. Engine code auto-detects (`torch_device()`): cuda → fp16 (CT2) / bf16 (transformers LLMs),
   cpu fallback stays for safety. Idle unload now also calls `torch.cuda.empty_cache()`.
4. **whisper.cpp deliberately stays CPU**: it is the arena's CPU-native C++ reference engine
   (building ggml with CUDA would change what the engine demonstrates). If full-GPU coverage is
   wanted anyway, rebuild with `-DGGML_CUDA=1` on an nvidia/cuda devel image.
5. Router gets `gpus: all` and reports the **real L40s** via nvidia-smi on the resource page
   (RAM pseudo-device remains as fallback when no GPU is visible).
6. On-demand loading + idle unload (600s) still applies — VRAM is only held while models are
   warm; `MAX_LOADED_VARIANTS=2` bounds whisper-family residency per engine.
