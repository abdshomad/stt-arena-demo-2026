# 002 — Engine → Real Model Mapping

Date: 2026-06-12

Per-engine decision. "Local" engines load genuinely different models on demand (CPU).
"API" engines call a real hosted API when their key exists in `.secrets`, otherwise report N/A.
"N/A" engines correspond to products that do not exist publicly (fictional 2026 names); they stay
gray/N/A unless the user later supplies a real backend.

## Local — genuine open models (16)

| Engine id | Real model loaded | Notes |
|---|---|---|
| `whisper` | `openai-whisper`, size selectable (tiny/base/small/medium/large-v3/large-v3-turbo) | default size `small` |
| `faster-whisper` | `faster-whisper` (CTranslate2), same sizes | default `small` |
| `whisperx` | `whisperx`, same sizes; pyannote diarization only if `HF_TOKEN` present | default `small` |
| `whisper.cpp` / `whisper-cpp` | whisper.cpp with ggml models (tiny/base/small/medium) | default `small` |
| `cahya-whisper-medium-id` | HF `cahya/whisper-medium-id` | Indonesian fine-tune |
| `cahya-whisper-small-id` | HF `cahya/whisper-small-id` | Indonesian fine-tune |
| `cahya-faster-whisper-medium-id` | `cahya/whisper-medium-id` converted to CTranslate2 at first load (cached) | conversion takes a few minutes once |
| `indonesian-nlp-wav2vec2-indonesian-javanese-sundanese` | HF `indonesian-nlp/wav2vec2-indonesian-javanese-sundanese` | CTC, no punctuation |
| `indonesian-nlp-wav2vec2-large-xlsr-indonesian` | HF `indonesian-nlp/wav2vec2-large-xlsr-indonesian` | CTC, no punctuation |
| `moonshine-voice` | HF `UsefulSensors/moonshine-base` via transformers | **English only** |
| `nvidia-parakeet-tdt-v3` | HF `nvidia/parakeet-tdt-0.6b-v3` via NeMo | multilingual (25 EU langs; no Indonesian) |
| `kyutai-stt` | HF `kyutai/stt-1b-en_fr` via moshi | EN/FR only; 1B chosen over 2.6B for CPU latency |
| `meta-omnilingual-asr` | `facebook/omnilingual-asr` CTC 300M variant | smallest variant for CPU; supports Indonesian |
| `voxtral-mini-4b-realtime` | HF `mistralai/Voxtral-Mini-3B-2507` via transformers | real model is 3B, not "4B"; slow on CPU |
| `google-ai-edge-eloquent` | HF `google/gemma-3n-E2B-it` (audio understanding) | "Eloquent" is fictional; Gemma 3n is Google's real edge audio model. **Gated on HF → needs `HF_TOKEN`**, else N/A |

## API-backed when key present in `.secrets` (4)

| Engine id | Real API used | Required key(s) |
|---|---|---|
| `gpt-realtime-whisper` | OpenAI `gpt-4o-transcribe` (fallback `whisper-1`) | `OPENAI_API_KEY` |
| `google-omni` | Gemini API audio understanding (`gemini-2.5-flash`) | `GEMINI_API_KEY` |
| `google-gemma-4-audio-understanding` | Gemini API (`gemini-2.5-flash-lite`) — "Gemma 4 audio" does not exist | `GEMINI_API_KEY` |
| `microsoft-vibe-voice-asr` | Azure AI Speech fast transcription — VibeVoice is a **TTS** model, not STT | `AZURE_SPEECH_KEY`, `AZURE_SPEECH_REGION` |

## N/A — no real public model or API exists (7)

`nvidia-nemotron-3.5-asr`, `nvidia-nemotron-omni`, `nvidia-personaplex-7b-v1`,
`nvidia-multitalker-asr`, `mega-asr`, `inword-ai-stt`, `srst`, `moss-sats-asr-with-diarization`

These names match no public model/API as of knowledge cutoff (Jan 2026). Their `/health`
reports `available: false, reason: "model does not exist publicly"`; `/transcribe` returns 503.
UI shows them gray with an N/A badge. If the user later identifies a real backend (e.g. an
NVIDIA NIM endpoint + `NVIDIA_API_KEY`), they can be wired the same way as the API group.

## Cloud SaaS alternatives sidebar (gcp-stt, aws-transcribe, elevenlabs-stt, deepgram-nova-2, openai-whisper-api, assembly-ai)

Not selectable in the arena (separate `CLOUD_ALTERNATIVES` list) → out of scope for this pass.
