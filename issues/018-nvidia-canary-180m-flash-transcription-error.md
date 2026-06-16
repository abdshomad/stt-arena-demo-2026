# Issue: nvidia-canary-180m-flash transcription failed

## Symptoms
When testing the `nvidia-canary-180m-flash` engine with `proklamasi.mp3`, the operation failed.
The test result output saved in `nvidia-canary-180m-flash-result.txt` recorded the following error:
```
HTTP 500 - {"detail":"nvidia-canary-180m-flash transcription failed: 'Hypothesis' object has no attribute 'strip'"}
```

## Root Cause
The engine returned an error during the `/transcribe` API request or while processing the model inference.

## Resolution
Needs investigation of the engine backend implementation logs and dependencies.
