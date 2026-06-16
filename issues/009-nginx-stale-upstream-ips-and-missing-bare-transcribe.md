# 009 — nginx 502 from stale engine IPs + bare /transcribe 404 made live mode silently fall back to mock

## Symptoms
- `POST http://localhost:5000/transcribe` → 404 (nginx tried to serve a static file `/etc/nginx/html/transcribe`).
- `POST http://localhost:5000/transcribe/whisper` with real audio → 502, nginx log: `connect() failed (111: Connection refused) while connecting to upstream 172.18.0.20:8001`.
- The app (ASR_MODE=live) posts to bare `/transcribe`; the 404 raised an axios error and `server.ts` silently answered with the "high-fidelity mockup" fallback — live mode never actually worked.

## Root Cause
1. nginx had only `/transcribe/<model-id>` prefix locations, but `server/sttService.ts` posts to the bare base URL with `modelId` as a form field.
2. nginx resolved engine container hostnames once at startup; after engine containers restarted with new IPs, the cached addresses went stale (no `resolver` directive).

## Resolution
`engines/nginx-router.conf` rewritten: `resolver 127.0.0.11 valid=10s` with variable `proxy_pass` targets (per-request DNS), all `/transcribe*` traffic routed to the router service which dispatches by `modelId` (including whisper size variants), long proxy timeouts for cold on-demand model loads, plus `/engines` and `/gpus` locations.
