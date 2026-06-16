# Issue: meta-omnilingual-asr transcription failed

## Symptoms
When testing the `meta-omnilingual-asr` engine with `proklamasi.mp3`, the operation failed.
The test result output saved in `meta-omnilingual-asr-result.txt` recorded the following error:
```
HTTP 500 - {"detail":"meta-omnilingual-asr transcription failed: The map function has failed while processing the path 'data' of the input data. See nested exception for details."}
```

## Root Cause
The engine returned an error during the `/transcribe` API request or while processing the model inference.

## Resolution
Needs investigation of the engine backend implementation logs and dependencies.
