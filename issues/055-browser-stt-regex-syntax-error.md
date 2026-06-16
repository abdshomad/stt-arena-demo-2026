# Issue: browser-stt regex template literal syntax error

## Symptoms
When building the Docker container or compiling the frontend code with `npm run build` after registering the Web Speech API and Transformers.js engines, the build failed with:
```
SyntaxError: missing ) after argument list
```
And:
```
[vite:esbuild] Transform failed with 1 error:
/app/src/data/modelsData.ts:1048:5: ERROR: Syntax error "n"
```

## Root Cause
1. A literal backtick (`` ` ``) was included inside a regular expression character group (`/[.,\\/#!$%\\^&\\*;:{}=\\-_`~()?]/g`) within a multiline template literal in `patch_app.cjs` and `bootstrap.ts`. The unescaped backtick terminated the template literal early, throwing a syntax parsing error at runtime.
2. The model entries join statement used `.join(',\\n')` with a double backslash in the patcher script, which printed a literal `\n` string into `src/data/modelsData.ts` instead of an actual newline character, breaking the JS object array syntax.

## Resolution
1. Replaced the regex backtick pattern with a safe concatenation/replacement using `String.fromCharCode(96)` (the ASCII value for backtick).
2. Fixed `.join(',\\n')` to `.join(',\n')` to print actual newlines into the generated models data file.
