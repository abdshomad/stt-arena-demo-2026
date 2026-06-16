# Issue: nvidia-nemotron-3.5-asr transcription failed

## Symptoms
When testing the `nvidia-nemotron-3.5-asr` engine with `proklamasi.mp3`, the operation failed.
The test result output saved in `nvidia-nemotron-3.5-asr-result.txt` recorded the following error:
```
HTTP 500 - {"detail":"nvidia-nemotron-3.5-asr transcription failed: 'TranscribeConfig' object has no attribute 'target_lang'"}
```

## Root Cause
The engine returned an error during the `/transcribe` API request or while processing the model inference.

## Resolution
The issue was fixed by modifying `engines/nvidia-nemotron-3.5-asr/main.py` to correctly construct and pass `HybridRNNTCTCPromptTranscribeConfig` with the target language code as `override_config` when calling `model.transcribe()`. This ensures NeMo's transcription pipeline resolves the prompt configuration correctly rather than falling back to the default `TranscribeConfig` which lacks the `target_lang` attribute.
