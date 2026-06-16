# Issue 007: WhisperX Engine ModuleNotFoundError: No module named 'whisper'

## Symptoms
The `stt-arena-nginx-router` container failed to start and threw the following error:
```
nginx: [emerg] host not found in upstream "whisperx-engine" in /etc/nginx/conf.d/default.conf:28
```
Upon checking `whisperx-engine` logs, the container was crashing repeatedly with:
```
ModuleNotFoundError: No module named 'whisper'
```

## Root Cause
A previous general patching script `patch_all_engines.py` was used to update backend engines. This script automatically replaced `main.py` of non-faster-whisper engines with a standard `whisper` model template. However, `whisperx-engine` uses a separate virtual environment containing the `whisperx` package (not `whisper`), causing a runtime crash on import.

## Resolution
1. Overwrote `engines/whisperx/main.py` with a custom implementation using the `whisperx` API:
   - Imported `whisperx` instead of `whisper`.
   - Utilized `whisperx.load_model` and `model.transcribe(audio, ...)` correctly.
2. Rebuilt the `whisperx-engine` docker image:
   ```bash
   docker compose up -d --build whisperx-engine
   ```
3. Restarted the Nginx gateway, state manager, and frontend:
   ```bash
   docker compose restart nginx-router router stt-arena
   ```
4. Confirmed all containers returned to a healthy state and verified proxy routes are operating correctly.
