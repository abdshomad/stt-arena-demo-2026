# Issue: nvidia-nemotron-3.5-asr transcription failed

## Symptoms
When testing the `nvidia-nemotron-3.5-asr` engine with `proklamasi.mp3`, the operation failed.
The test result output saved in `nvidia-nemotron-3.5-asr-result.txt` recorded the following error:
```
HTTP 500 - {"detail":"nvidia-nemotron-3.5-asr transcription failed: Sizes of tensors must match except in dimension 2. Expected size 608 but got size 607 for tensor number 1 in the list."}
```

## Root Cause
The engine returned an error during the `/transcribe` API request or while processing the model inference.

## Resolution
The issue was resolved by modifying the `forward` method of the dynamically registered `EncDecRNNTBPEModelWithPrompt` class in `engines/nvidia-nemotron-3.5-asr/main.py`. The code now handles both prompt truncation (when the prompt is longer than the encoded tensor in the time dimension) and padding (when the prompt is shorter than the encoded tensor). Specifically, when `prompt.shape[1] < encoded.shape[1]`, the prompt is padded with zeros along dimension 1 (time) using `torch.cat` to match `encoded.shape[1]` exactly before concatenation. The container was then rebuilt and restarted, which successfully resolved the error.
