# 006 — Honesty Cleanups: Diarization, Emotion, Fallbacks

Date: 2026-06-12

1. **Fake alternating speakers removed**: engines used `speakerId = idx % 2` to simulate
   diarization. Now all segments report `speakerId: 0` unless the engine performs real
   diarization (whisperx + pyannote when `HF_TOKEN` is set).
2. **The existing patch forcing "SOTA diarization" for every model** (patch_app.cjs patches #2
   and #3) is replaced with capability data that reflects reality: whisperx = real diarization
   (when HF_TOKEN present), everything else = none. Assumption: the user prefers honesty over
   the previous cosmetic patch, given the stated goal. If the SOTA-everywhere look is still
   wanted, revert this part of patch_app.cjs.
3. **Emotion detection** stays a keyword heuristic applied to the *real* transcript, only for
   models flagged `emotionDetection`, and is labeled "heuristic" in the response
   (`detectedEmotion: "<label> (heuristic)"`). No engine in the lineup actually does SER.
4. **Mock fallback visibility**: any response with `mode: "mockup"` reaching the arena renders
   with a clear "SIMULATED — engine unreachable" banner instead of being indistinguishable from
   live output.
