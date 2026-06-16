# 011 — transformers engines failed: "Could not import module 'pipeline'"

## Symptoms
All transformers-based engines (cahya whisper ID, wav2vec2, moonshine, kyutai, voxtral) returned
`{"detail": "... Could not import module 'pipeline'. Are this object's requirements defined correctly?"}`
on every transcription request.

## Root Cause
The `stt-arena-base:transformers` image installed `torch`/`torchaudio` from the PyTorch CPU
wheel index first, then `timm` (added for Gemma 3n) pulled `torchvision` from PyPI built against
CUDA torch. The mismatched pair raised `RuntimeError: operator torchvision::nms does not exist`
inside transformers' lazy import, which surfaces as the misleading "Could not import module
'pipeline'" message.

## Resolution
Bases rebuilt for the GPU migration with a **single pip resolve** installing
`torch torchvision torchaudio` together from PyPI (CUDA builds, version-matched), eliminating
the mismatch. Verified by importing `transformers.pipeline` in the rebuilt image.
