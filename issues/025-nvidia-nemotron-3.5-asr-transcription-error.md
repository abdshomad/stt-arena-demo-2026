# Issue: nvidia-nemotron-3.5-asr transcription failed

## Symptoms
When testing the `nvidia-nemotron-3.5-asr` engine with `proklamasi.mp3`, the operation failed.
The test result output saved in `nvidia-nemotron-3.5-asr-result.txt` recorded the following error:
```
HTTP 500 - {"detail":"nvidia-nemotron-3.5-asr transcription failed: EncDecRNNTModel.transcribe() got an unexpected keyword argument 'target_lang'"}
```

## Root Cause
The engine returned an error during the `/transcribe` API request or while processing the model inference.

## Resolution
The issue was fixed by modifying the transcription logic in `engines/nvidia-nemotron-3.5-asr/main.py`:
1. Corrected dynamic class registration for the custom NeMo model by assigning `asr_models.rnnt_bpe_models_prompt = m_module` on the parent module, setting `__module__` and `__qualname__` properly, and implementing missing abstract methods required for class instantiation.
2. Removed the unsupported `target_lang` parameter from the `model.transcribe()` call, as `EncDecRNNTModel` does not support it.
3. Rebuilt and restarted the `nvidia-nemotron-3.5-asr-engine` docker container.
