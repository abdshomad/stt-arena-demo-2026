# Issue: patch_app.cjs Unescaped Backticks and Over-broad Filesystem Interception

## Symptoms
1. The Docker build process failed at step `RUN node patch_app.cjs` with:
   `SyntaxError: missing ) after argument list` at line 66 (triggered by an unescaped backtick in the template literal at line 386) and subsequently line 540.
2. The Node.js dev server crashed with:
   `Error: Transform failed with 1 error: bootstrap.ts:756:19: ERROR: Expected ";" but found "📥"`
   when file readers/compilers read files in the workspace.

## Root Cause
1. **Unescaped Backticks in Template Literals**: `patch_app.cjs` defined large template literals representing the code to patch into `App.tsx`. Inside these template literals, unescaped backticks (such as in `onLog(`📥 ...`)` at line 386 and `fetchModelWithCache(...)` at line 540) terminated the template literal early, leading to invalid syntax and parser failures when Node.js compiled `patch_app.cjs`.
2. **Over-broad FS Interception**: The filesystem hooks (`fs.readFileSync`, `fs.readFile`, and `fs.promises.readFile`) in `bootstrap.ts` intercepted reads for *all* files under the workspace root, applying newline normalization `normalizeNewlines(content)` to them. This changed CRLF line endings to LF on unrelated files like `bootstrap.ts`, causing cached token/sourcemap offsets in `tsx`'s internal memory to mismatch, which triggered unexpected syntax errors at runtime.

## Resolution
1. **Syntax Fixes in patch_app.cjs**: Replaced the unescaped backtick logs and function arguments in `patch_app.cjs` (at lines 386, 540, and 594) with double-quoted strings and `+` concatenation.
2. **Path Filtering in bootstrap.ts Hook**: Introduced a helper function `shouldPatch` in `bootstrap.ts` to restrict the filesystem interception only to the specific files targeted by our patches (e.g. `App.tsx`, `ModelCard.tsx`, `DialogueArena.tsx`, etc.). All other workspace files are returned immediately and completely unmodified, preventing encoding or line-ending mismatches.
