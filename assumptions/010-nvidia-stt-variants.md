# 010 — NVIDIA STT Variants and Provider Grouping

Date: 2026-06-12

## User decisions
- Implement all NVIDIA speech-to-text (ASR) variants.
- Group the model cards/options by provider (e.g. Whisper Models, NVIDIA Models, Meta Models, Google Models, Microsoft Models, Indonesian Fine-Tuned Models, and Other Models) in the UI.

## Design
1. **Real NVIDIA Model Implementations**:
   - **Nemotron ASR**: Replaced the mockup of `nvidia-nemotron-3.5-asr` with a real loader for `nvidia/nemotron-3.5-asr-streaming-0.6b`. Added `nvidia-nemotron-speech-streaming-en` to run the streaming-optimized `nvidia/nemotron-speech-streaming-en-0.6b` model.
   - **Canary Multilingual Models**: Added `nvidia-canary-1b-v2` (1B parameters, 25 languages) and `nvidia-canary-180m-flash` (180M parameters, 4 languages) running locally using NeMo's `EncDecMultiTaskModel` class.
   - **Parakeet Family**: Added `nvidia-parakeet-ctc-0.6b` (CTC decoder, 600M parameters) and `nvidia-parakeet-rnnt-1.1b` (RNNT decoder, 1.1B parameters, Enterprise Riva NIM equivalent). These run alongside the existing `nvidia-parakeet-tdt-v3` (TDT decoder, 600M parameters).
   - **MultiTalker ASR**: Replaced the mockup of `nvidia-multitalker-asr` with a real loader for `nvidia/multitalker-parakeet-streaming-0.6b-v1` supporting overlapping multi-speaker transcription.
   - **Gated / Heavy Models (N/A)**: `nvidia-nemotron-omni` (a 30B MoE multimodal LLM) and `nvidia-personaplex-7b-v1` (a gated, full-duplex conversational model requiring HuggingFace authorization/token validation) remain flagged as `available=false` (N/A) with explicit reason cards.
2. **GPU Load Balancing**:
   - Pinned the heavy models (`canary-1b-v2` at 4.0 GB VRAM, `parakeet-rnnt-1.1b` at 4.5 GB VRAM) to CUDA GPU 1, and balanced the lighter models (`canary-180m-flash`, `parakeet-ctc-0.6b`, `nemotron-speech-streaming-en`) on CUDA GPU 0 in `docker-compose.yml` and `engines/router/main.py`.
3. **UI Provider Grouping**:
   - **Selection Dropdowns**: Added `renderGroupedOptions` to `src/App.tsx` utilizing `<optgroup>` elements to separate and categorize models by provider (Whisper, NVIDIA, Google, Meta, Microsoft, Indonesian Fine-Tuned, Other).
   - **Model Card Catalog Grid**: Categorized the GPU Model Manager catalog list in `GpuModelManager.tsx` to group model cards by provider under clear headers.
