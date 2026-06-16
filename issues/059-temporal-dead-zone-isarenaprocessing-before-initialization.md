# Issue: Temporal Dead Zone (TDZ) - Cannot access 'isArenaProcessing' before initialization

## Symptoms
The browser loaded a blank screen and logged the following error to the console:
```
PAGE ERROR: Cannot access 'isArenaProcessing' before initialization
```

## Root Cause
In `src/App.tsx`, `isArenaProcessing` state is declared on line 273.
However, the `availability-state` patch in both `bootstrap.ts` and `patch_app.cjs` inserted state variables and a `useEffect` hook referencing `isArenaProcessing` immediately after the `customUploadedSample` state declaration, which occurs on line 268.
Because the hook was defined and closed over `isArenaProcessing` before the latter was initialized by React, it triggered a JavaScript Temporal Dead Zone ReferenceError at startup.

## Resolution
Modified the target of the `availability-state` patch in both `bootstrap.ts` and `patch_app.cjs` to target `copiedCodeTab` (which is declared on line 281, after all the other arena states). This ensures all dependent state variables are fully initialized before the hooks run.
