# Issue: kyutai-stt transcription failed

## Symptoms
When testing the `kyutai-stt` engine with `proklamasi.mp3`, the operation failed.
The test result output saved in `kyutai-stt-result.txt` recorded the following error:
```
HTTP 500 - {"detail":"kyutai-stt transcription failed: 'NoneType' object has no attribute 'shape'"}
```

## Root Cause
The engine returned an error during the `/transcribe` API request or while processing the model inference.

## Resolution
Needs investigation of the engine backend implementation logs and dependencies.
