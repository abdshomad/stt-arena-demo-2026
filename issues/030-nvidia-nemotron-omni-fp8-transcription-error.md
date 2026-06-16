# Issue: nvidia-nemotron-omni-fp8 transcription failed

## Symptoms
When testing the `nvidia-nemotron-omni-fp8` engine with `proklamasi.mp3`, the operation failed.
The test result output saved in `nvidia-nemotron-omni-fp8-result.txt` recorded the following error:
```
HTTP 502 - {"detail":"engine 'nvidia-nemotron-omni-fp8' unreachable: All connection attempts failed"}
```

## Root Cause
The engine returned an error during the `/transcribe` API request or while processing the model inference.

## Resolution
Needs investigation of the engine backend implementation logs and dependencies.
