# 001 — Scope and User Decisions

Date: 2026-06-12

## Confirmed by user (AskUserQuestion answers)

1. **Scope**: Replace every impostor engine with its genuine open model where one exists ("Real models where possible").
2. **Engines whose claimed model doesn't exist / isn't locally runnable**: back them with a real API using keys the user will add to `.secrets`; while the key is absent (or no real API exists at all), the model is shown **grayed out with an "N/A" flag** in the UI.
3. **Compute**: **On-demand loading** — engines start empty, load their model at first request, and unload after idle timeout. CPU inference (both L40 GPUs are occupied by other workloads).
4. **Whisper sizes**: user can choose sizes, and different sizes can battle each other in the arena.

## Standing instruction

> "when im not answering, proceed with your best assumptions, and write the assumptions in /assumptions/ folder with file numberings"

All subsequent files in this folder document those assumptions.

## Baseline findings that motivated the work

- All 27 "engines" secretly ran `whisper tiny` (or its faster-whisper/whisperx/ggml equivalent) and merely labeled the JSON response with the brand name.
- The arena UI never sent audio: it POSTed the scripted transcript as `text`, and every engine's JSON branch **echoed that text back** — 0% real transcription.
- Even that fake path was broken: the app posts to bare `/transcribe` on nginx-router, which only had `/transcribe/<model-id>` locations → 404 → silent "high-fidelity mockup" fallback in `server.ts`.
- nginx resolved engine container IPs at startup; they went stale → 502 on direct engine routes.
