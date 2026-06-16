# 010 — Engine /health timed out while a model was loading/transcribing

## Symptoms
`/engines/health` reported `available:false, reason:"engine unreachable: ReadTimeout"` for engines that were actually fine but busy with a first-request on-demand model load — the UI would have shown healthy engines as N/A whenever they were warming up.

## Root Cause
`engine_common.py`'s `/transcribe` endpoint is `async def` but called the blocking model `load()`/`transcribe()` callables directly, freezing uvicorn's event loop for the duration (minutes for big downloads), so concurrent `/health` requests couldn't be answered.

## Resolution
Blocking work (ffmpeg conversion, model load, inference) moved off the event loop with `asyncio.to_thread(...)` in `/transcribe` and `/load`. `/health` now responds during loads and reports the `loading` flag instead of appearing dead.
