# 003 — Real Audio Pipeline (arena must send audio, not text)

Date: 2026-06-12

## Problem

The arena battle flow sent the *scripted transcript* as `text` and engines echoed it back.
Real STT requires real audio end to end.

## Decisions

1. **Engines reject text-only requests.** The JSON echo branch is removed from every engine.
   `/transcribe` accepts only multipart with a `file` field; JSON-only requests get HTTP 400
   ("audio file required — text echo mode removed"). This makes silent fakery impossible.
2. **The frontend sends audio whenever the active sample has it** (patched via `patch_app.cjs`,
   never editing the submodule working tree — patches run on the copy inside the Docker build):
   - Custom uploaded audio (`CustomAudioUploader`) and live mic recordings already produce a
     blob/objectURL → battle fetches the blob and POSTs `FormData` (file + modelId + language).
   - A **bundled real sample** is added: `proklamasi.mp3` (Indonesian, Proklamasi Kemerdekaan
     recording present in repo root), served as a static asset, with the official proclamation
     text as reference transcript for WER display.
3. **Scripted samples without audio** (the existing text-only samples and dialogue profiles)
   cannot be truly transcribed. In live mode they are labeled "Scripted — no audio (simulated)"
   in the sample picker; if used, the response comes from the existing mock path and the UI
   keeps showing the existing fallback warning. We do NOT synthesize TTS audio for them (out of
   scope; could be a follow-up).
4. **Routing fix**: nginx gets `location = /transcribe` → router service, which dispatches by
   the `modelId` form field (dispatch code already existed). Per-model nginx locations stay.
   nginx upstreams switch to Docker's internal DNS resolver (`resolver 127.0.0.11 valid=10s`)
   with variable proxy_pass targets so engine restarts don't leave stale IPs (fixes the 502s).
5. `server.ts` mock fallback stays as a safety net but its responses are already flagged
   (`mode: "mockup"`, `fallbackWarning`) — the UI will surface that flag visibly on the result
   card so a fallback can never be mistaken for a real transcription.
