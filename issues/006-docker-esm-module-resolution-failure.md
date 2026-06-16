# Issue 006: ES Module Scope Resolution Failure during Docker Build

## Symptoms
Rebuilding the Docker containers using `docker compose up -d --build` failed with the following traceback during the frontend asset patching stage:
```
ReferenceError: require is not defined in ES module scope, you can use import instead
This file is being treated as an ES module because it has a '.js' file extension and '/app/package.json' contains "type": "module". To treat it as a CommonJS script, rename it to use the '.cjs' file extension.
    at file:///app/patch_app.js:1:12
```

## Root Cause
The `patch_app.js` file used Node.js `require('fs')` (CommonJS module syntax). However, the working directory inside the container `/app` had a `package.json` file specifying `"type": "module"`. As a result, Node.js treated all `.js` files in that directory as ES Modules by default, throwing a `ReferenceError` on the CJS-only `require` keyword.

## Resolution
Renamed `patch_app.js` to `patch_app.cjs` on the host, updated the `Dockerfile` to copy and execute `patch_app.cjs`, and rebuilt the Docker image. Because of the `.cjs` extension, Node.js correctly forced the script to load in CommonJS mode, bypassing the root ES Module scope constraint and executing successfully.
