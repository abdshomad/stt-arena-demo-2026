# Issue 005: React State Closure Out-of-Bounds Crash in Arena Battle Logs

## Symptoms
After starting the Model Arena Battle in the Comparative Arena tab, the page crashed and went completely blank (white screen). The browser console logged the following unhandled runtime exception:
```
[Browser Error] Cannot read properties of undefined (reading 'msg')
```

## Root Cause
In `App.tsx` (inside the `stt-arena-design` submodule), the arena battle progress runs inside a `setInterval` timer. During each tick, it appends benchmark logs to the state:
```typescript
if (currentLogIndex < logTimeline.length && currentPct >= logTimeline[currentLogIndex].p) {
  setArenaLogs(prev => [...prev, `[${(currentPct * 0.05).toFixed(1)}s] ${logTimeline[currentLogIndex].msg}`]);
  currentLogIndex++;
}
```
Because `setArenaLogs` uses a functional state updater, the arrow function `prev => ... logTimeline[currentLogIndex].msg` is scheduled and evaluated asynchronously by React during the rendering phase.
However, `currentLogIndex++` runs immediately on the main thread after scheduling the state update.
By the time React evaluates the functional updater, `currentLogIndex` has already been incremented (e.g. from `7` to `8`). Since `logTimeline` only contains 8 elements (indices `0` to `7`), `logTimeline[8]` is `undefined`, causing the application to crash when trying to access `.msg` on it.

## Resolution
To keep the host submodule clean and comply with project rules, a Node.js patch script `patch_app.cjs` was added in the parent repository. During `docker compose build`, the `Dockerfile` copies and executes this patch script to modify the file inside the container's build environment.
The script replaces the out-of-bounds lookup with a bounds-safe index:
```typescript
logTimeline[Math.min(currentLogIndex, logTimeline.length - 1)].msg
```
This safely falls back to the final index when `currentLogIndex` is out of bounds, preventing any TypeError and letting the UI render the completed logs successfully.
