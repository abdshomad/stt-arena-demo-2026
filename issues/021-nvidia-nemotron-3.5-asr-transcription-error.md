# Issue: nvidia-nemotron-3.5-asr transcription failed

## Symptoms
When testing the `nvidia-nemotron-3.5-asr` engine with `proklamasi.mp3`, the operation failed.
The test result output saved in `nvidia-nemotron-3.5-asr-result.txt` recorded the following error:
```
HTTP 500 - {"detail":"nvidia-nemotron-3.5-asr transcription failed: Can't instantiate abstract class ASRModel with abstract methods setup_training_data, setup_validation_data"}
```

## Root Cause
The engine returned an error during the `/transcribe` API request or while processing the model inference.

## Resolution
Needs investigation of the engine backend implementation logs and dependencies.
