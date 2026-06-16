# Issue: Duplicate Keys Warning During Browser Models Merge

## Symptoms
The browser console displayed warnings about duplicate keys when rendering the Model Catalog grid:
```
PAGE LOG: Encountered two children with the same key, browser-web-speech-api. Keys should be unique...
```

## Root Cause
The Express backend endpoint `/api/gpus` returns a list of models which already includes the browser models (e.g. `browser-web-speech-api`, `browser-vosk`, etc.).
In `GpuModelManager.tsx`, the patched code merged the backend list and the local `browserModels` list by simple concatenation:
```typescript
const merged = [...data.models, ...browserModels].map(...)
```
This produced duplicate model entries in the array, causing React to render duplicate list items with identical `key={model.id}` properties.

## Resolution
Modified the merge block in both `bootstrap.ts` and `patch_app.cjs` to filter out any model from `browserModels` that is already present in `data.models`:
```typescript
const merged = [...data.models, ...browserModels.filter((bm: any) => !data.models.some((m: any) => m.id === bm.id))].map(...)
```
This deduplicates the models list before rendering, resolving the unique key warning.
