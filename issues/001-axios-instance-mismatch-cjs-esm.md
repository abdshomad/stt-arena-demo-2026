# Issue 001: Axios Instance Mismatch between ESM and CommonJS in Production Container

## Symptoms
ASR / STT transcription requests made through the frontend application UI failed to route to the correct Whisper-based backend engines and instead fell back to the high-fidelity mock database. The Nginx router logs showed that it received requests to `POST /transcribe` (which resulted in 404) instead of targeted URLs like `POST /transcribe/whisper` or `POST /transcribe/faster-whisper`.

## Root Cause
1. The frontend server compiled by Vite/esbuild runs from `dist/server.cjs` which is a CommonJS module.
2. In the Docker container, the entry point ran `dist/server.cjs` directly without loading the `bootstrap` patch.
3. Even after configuring the entry point to run `bootstrap.js` (using ES Modules), the `import axios from 'axios'` in `bootstrap.js` loaded the ESM instance of the Axios package, whereas the `require('axios')` inside `dist/server.cjs` loaded the CommonJS instance of Axios. 
4. Because Node.js resolves ESM and CommonJS packages separately under certain configurations, monkeypatching the ESM `axios` instance in `bootstrap.js` did not affect the CommonJS `axios` instance required by the compiled server code.

## Resolution
Modified `bootstrap.js` and `bootstrap.ts` to require the CommonJS version of Axios using `module.createRequire` and apply the exact same `axios.post` proxy/intercept patch to both the ESM and CJS Axios instances:
```javascript
try {
  const cjsAxios = require('axios');
  if (cjsAxios && cjsAxios !== axios) {
    patchAxiosInstance(cjsAxios, 'CJS');
  }
} catch (err) {
  console.warn("Could not patch CJS axios instance:", err);
}
```
Rebuilt the frontend docker image and verified that requests are now rewritten correctly.
