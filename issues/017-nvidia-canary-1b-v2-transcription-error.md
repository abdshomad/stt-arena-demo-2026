# Issue: nvidia-canary-1b-v2 transcription failed

## Symptoms
When testing the `nvidia-canary-1b-v2` engine with `proklamasi.mp3`, the operation failed.
The test result output saved in `nvidia-canary-1b-v2-result.txt` recorded the following error:
```
HTTP 500 - {"detail":"nvidia-canary-1b-v2 transcription failed: 'Hypothesis' object has no attribute 'strip'"}
```

## Root Cause
The engine returned an error during the `/transcribe` API request or while processing the model inference.

## Resolution
Needs investigation of the engine backend implementation logs and dependencies.
