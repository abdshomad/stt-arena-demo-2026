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
The issue was resolved by correcting the processor call in `engines/kyutai-stt/main.py`. The upgraded `transformers` library's `KyutaiSpeechToTextProcessor.__call__` has `images` as its first parameter, pushing the positional arguments. Restoring the explicit `audio=audio` keyword argument ensures the input features are correctly prepared and prevents `NoneType` errors on the input tensor shape. The `kyutai-stt-engine` docker container was rebuilt and restarted.
