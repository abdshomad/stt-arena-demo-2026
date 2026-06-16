# Multi-Step Refactoring Instructions for Git Submodule Agent (`stt-arena-design`)

## Context & Goal
We want to modify the `stt-arena-design` repository to natively support **Browser-Based client-side Speech-To-Text (STT) models and runtimes** (such as WebAssembly / WASM, native browser APIs, and in-browser inference engines). 

Currently, the parent repository uses complex in-memory regex string replacement hacks (`bootstrap.ts` and `patch_app.cjs`) to inject these features on top of your build. Natively integrating these features into your repo will make these heavy patches obsolete.

You will implement this refactoring in **5 incremental phases**. After completing each phase, do NOT proceed further. Instead, present your changes, confirm they compile cleanly, and wait for the user to type **"next"** before beginning the next phase.

---

## Phase 1: Database & Model Types
**Goal**: Native metadata fields and model registration.

1. **Modify `src/types/gpu.ts`**:
   Add the following optional fields to `ManagedModel` interface to track browser-based lifecycles:
   - `downloadSizeMb?: number;` — Metadata for the model's download size.
   - `status: 'unloaded' | 'loading' | 'loaded';` — Model lifecycle state.
   - `progress?: number;` — Current download/loading percentage.

2. **Modify `src/data/modelsData.ts`**:
   Add the browser-based models to the catalog of available models. Set their `sourceType` to `'Browser / WASM'` or `'Browser / Native'` and define appropriate `downloadSizeMb` values:
   - **Web Speech API**: ID `browser-web-speech-api`, Native API format, always loaded, 0 MB.
   - **Transformers.js (Whisper Tiny)**: ID `browser-transformers-js`, WASM/ONNX format, 75 MB.
   - **whisper.cpp (Tiny EN, Base EN, Base Multilingual)**: WASM/ggml formats, 75 MB, 142 MB, 142 MB.
   - **whisper.cpp Quantized (Tiny EN Q5_1, Base EN Q5_1)**: WASM/ggml formats, 31 MB, 57 MB.
   - **Mozilla DeepSpeech**: ID `browser-mozilla-deepspeech`, WASM format, 180 MB.
   - **Baidu DeepSpeech**: ID `browser-baidu-deepspeech`, WASM format, 220 MB.
   - **Vosk**: ID `browser-vosk`, WASM format, 50 MB.
   - **Picovoice**: ID `browser-picovoice`, WASM format, 5 MB.

*Stop here. Report your changes, verify they compile, and wait for the user to say **"next"**.*

---

## Phase 2: Model Registry UI (`ModelCard.tsx` & `GpuModelManager.tsx`)
**Goal**: Integrate browser model loading status and catalog groupings.

1. **Modify `src/components/ModelCard.tsx`**:
   - If the model is a browser model (e.g. `id.startsWith('browser-')`), render `Download: X MB` instead of `Size: Y GB`.
   - Implement lifecycle controls in the card footer:
     - Render **"Load Model in Browser"** (green button) if status is `'unloaded'`.
     - Render a loading progress bar with percentage if status is `'loading'`.
     - Render **"Loaded in Browser"** tag alongside an **"Unload from Browser"** button if status is `'loaded'`.

2. **Modify `src/components/GpuModelManager.tsx`**:
   - Group the catalog model grid into 7 visual categories: *Whisper Models*, *NVIDIA Models*, *Meta Models*, *Google Models*, *Microsoft Models*, *Browser-Based Engines*, and *Other Models*.
   - Add **"Load All Engines"** and **"Unload All Engines"** buttons in the headers of these groups to support bulk operations.
   - Add a `'Browser'` option to the `filterSourceType` select filter.
   - In the models fetch merge block, ensure local browser models are merged with backend models dynamically, avoiding duplicate item keys if the backend already returns them.

*Stop here. Report your changes, verify they compile, and wait for the user to say **"next"**.*

---

## Phase 3: Client-Side Execution Framework (`src/App.tsx`)
**Goal**: Dynamic UI integration, dropdown grouping, latency tracking, and mic recording.

1. **Comparative Arena Model dropdowns**:
   - Group the selection options in both Fighter dropdowns into `optgroup` elements according to their families (Whisper, NVIDIA, Google, Meta, Microsoft, Browser, and Other).
   - If a model is not active/available (check health endpoint availability), disable it in the dropdown.

2. **Microphone Live Recording**:
   - Natively bind the live microphone recording feature using `MediaRecorder` API to capture WAV blobs.
   - Simultaneously use native browser `SpeechRecognition` API (if available) to capture live transcripts.
   - Feed completed recordings as custom audio samples.

3. **Measured Latency Outcome Cards**:
   - Ensure the arena battle initiates client-side runtimes for browser models instead of making POST requests to `/api/transcribe`.
   - Measure the actual client-side latency using `performance.now()`.
   - Render the measured latency (labeled as `(Measured)`) in both outcome cards and use it to dynamically evaluate the latency winner in the verdict card.

*Stop here. Report your changes, verify they compile, and wait for the user to say **"next"**.*

---

## Phase 4: In-Browser STT Runtimes
**Goal**: Real client-side runners.

In `src/App.tsx`, implement the client-side execution loops:
1. **Web Speech API**: Call the native SpeechRecognition API with the target language.
2. **Transformers.js**: Dynamically import `@xenova/transformers` from CDN, download and initialize the model, resample the audio buffer to 16kHz, and perform inference.
3. **whisper.cpp WASM**: Dynamically load the Emscripten runtime, fetch the ggml models, cache them in IndexedDB, Resample audio to 16kHz mono, and pipe it through the WASM instance.
4. **Offline Simulators (DeepSpeech / Vosk / Picovoice)**: Write local simulators that mimic loading, audio parsing, client-side decoding, and generate transcripts.

*Stop here. Report your changes, verify they compile, and wait for the user to say **"next"**.*

---

## Phase 5: Resource Load Utilization & Sparklines
**Goal**: Simulating browser load during client-side runtimes.

1. **Resource Simulation**:
   - Add state hooks for `cpuLoad`, `gpuLoad`, `cpuHistory`, and `gpuHistory`.
   - When a browser model starts transcribing, start a resource simulation timer.
   - WASM runtimes should simulate high CPU utilization (70–95%) and low GPU (1-5%). Native APIs should simulate lower usage (15–30%).

2. **Sparkline Visualization**:
   - Write a helper to render a small text-based sparkline graph from historical values (e.g. mapping CPU history array values to block characters ` ▂▃▄▅▆▇█`).
   - Append the current resource load and the unicode sparkline history inside the CLI Simulation Console log panel when a browser battle is active.

*Stop here. Report your changes, verify they compile, and wait for the user to say **"next"**.*

---

## Phase 6: Clean Up Parent Repo
**Goal**: Eliminate parent repo dynamic patches.

Now that `stt-arena-design` natively supports all client-side models, loading, execution, resource graphs, and sparklines:
1. Inspect the parent repository's `bootstrap.ts` and `patch_app.cjs`.
2. Strip out all code replacements, file reader interception hooks, and target filters that were performing React component updates on `stt-arena-design` files.
3. Clean up parent files and verify that the application compiles cleanly.
