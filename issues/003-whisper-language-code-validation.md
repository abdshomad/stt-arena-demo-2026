# Issue 003: Whisper Engine Language Code Validation Crash (ValueError)

## Symptoms
ASR transcription requests routed to the `faster-whisper-engine` and `whisperx-engine` failed with status code 500. Container logs showed the following error traceback:
`ValueError: 'English' is not a valid language code (accepted language codes: af, am, ar, as, ...)`

## Root Cause
The frontend server forwards the language preference as a full name string, such as `"English"` or `"Indonesian"`. While the standard OpenAI Whisper python library automatically maps these to short ISO-639-1 language codes (e.g. `"en"`, `"id"`), `faster-whisper` and `whisperx` validate language inputs strictly against the ISO codes and throw a `ValueError` for full names.

## Resolution
Modified the FastAPI `main.py` entrypoints for `faster-whisper`, `whisperx`, and `whisper-cpp` to map full-length language names dynamically to their respective short codes:
```python
if language:
    lang_lower = language.lower().strip()
    if lang_lower == "english":
        language = "en"
    elif lang_lower == "indonesian":
        language = "id"
```
Rebuilt the images and verified the engines transcribe correctly.
