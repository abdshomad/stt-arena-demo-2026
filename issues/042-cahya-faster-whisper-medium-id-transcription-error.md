# Issue: cahya-faster-whisper-medium-id transcription failed

## Symptoms
When testing the `cahya-faster-whisper-medium-id` engine with `proklamasi.mp3`, the operation failed.
The test result output saved in `cahya-faster-whisper-medium-id-result.txt` recorded the following error:
```
HTTP 502 - <html>
<head><title>502 Bad Gateway</title></head>
<body>
<center><h1>502 Bad Gateway</h1></center>
<hr><center>nginx/1.29.4</center>
</body>
</html>

```

## Root Cause
The engine returned an error during the `/transcribe` API request or while processing the model inference.

## Resolution
Needs investigation of the engine backend implementation logs and dependencies.
