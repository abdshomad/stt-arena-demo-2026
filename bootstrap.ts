import { createRequire } from 'module';
const require = createRequire(import.meta.url);

import fs from 'fs';
import path from 'path';
import promises from 'fs/promises';

// Store original methods
const originalReadFileSync = fs.readFileSync;
const originalReadFile = fs.readFile;
const originalPromisesReadFile = fs.promises.readFile;

function normalizeNewlines(str: string): string {
  return str.replace(/\r\n/g, '\n');
}

function getRelativePath(absoluteOrRelativePath: any): string {
  if (typeof absoluteOrRelativePath !== 'string') {
    return '';
  }
  const resolved = path.resolve(absoluteOrRelativePath);
  const rootDir = '/home/aiserver/LABS/AI-VOICE/stt-arena-demo-2026';
  if (resolved.startsWith(rootDir)) {
    return path.relative(rootDir, resolved).replace(/\\/g, '/');
  }
  return '';
}

function applyPatches(filePath: string, content: string): string {
  const relPath = getRelativePath(filePath);
  if (!relPath) return content;

  let patched = normalizeNewlines(content);

  if (relPath.endsWith('stt-arena-design/server.ts') || relPath.endsWith('server.ts')) {
    console.log("[Bootstrap FS-Hook] Patching server.ts...");
    
    // engine-health-proxy
    patched = patched.replace(
      '// GET active list of cluster GPUs and model registers',
      `// Aggregated live engine availability — drives gray/N-A flags in the UI
app.get("/api/engines/health", async (_req, res) => {
  try {
    const axios = (await import("axios")).default;
    const healthUrl = process.env.REAL_ENGINE_HEALTH_URL || "http://localhost:5000/engines/health";
    const r = await axios.get(healthUrl, { timeout: 5000 });
    res.json(r.data);
  } catch (err: any) {
    res.json({ engines: {}, error: err.message });
  }
});

// GET active list of cluster GPUs and model registers`
    );
  }
  else if (relPath.endsWith('stt-arena-design/server/sttService.ts') || relPath.endsWith('server/sttService.ts')) {
    console.log("[Bootstrap FS-Hook] Patching server/sttService.ts...");
    
    // forward-timeout
    patched = patched.replace(
      'timeout: 30000 // 30 seconds max timeout',
      'timeout: 1800000 // 30 minutes: cold on-demand model loads on CPU are slow'
    );
    
    // diarization-honest-server
    patched = patched.replace(
      'const supportsDiarization = modelId === "elevenlabs-stt" || modelId === "gcp-stt" || modelId === "assembly-ai" || modelId.includes("omni") || modelId.includes("diarization");',
      'const supportsDiarization = modelId.includes("whisperx");'
    );
  }
  else if (relPath.endsWith('stt-arena-design/src/App.tsx') || relPath.endsWith('src/App.tsx')) {
    console.log("[Bootstrap FS-Hook] Patching src/App.tsx...");
    
    // closure-bug
    patched = patched.replace(
      'setArenaLogs(prev => [...prev, `[${(currentPct * 0.05).toFixed(1)}s] ${logTimeline[currentLogIndex].msg}`]);',
      'const logMsg = logTimeline[currentLogIndex]?.msg; if (logMsg) { setArenaLogs(prev => [...prev, `[${(currentPct * 0.05).toFixed(1)}s] ${logMsg}`]); }'
    );
  }

  return patched;
}

function shouldPatch(relPath: string): boolean {
  const normalized = relPath.replace(/\\/g, '/');
  return normalized.endsWith('stt-arena-design/server.ts') || normalized.endsWith('server.ts') ||
         normalized.endsWith('stt-arena-design/server/sttService.ts') || normalized.endsWith('server/sttService.ts') ||
         normalized.endsWith('stt-arena-design/src/App.tsx') || normalized.endsWith('src/App.tsx');
}

// 1. readFileSync Hook
fs.readFileSync = function (this: any, pathArg: any, options?: any) {
  const result = originalReadFileSync.call(fs, pathArg, options);
  const relPath = getRelativePath(pathArg);
  if (relPath && shouldPatch(relPath)) {
    const originalContent = typeof result === 'string' ? result : result.toString('utf8');
    const patchedContent = applyPatches(pathArg, originalContent);
    if (typeof result === 'string') {
      return patchedContent;
    }
    return Buffer.from(patchedContent, 'utf8');
  }
  return result;
} as any;

// 2. readFile Hook
fs.readFile = function (this: any, pathArg: any, options: any, callback?: any) {
  let actualOptions = options;
  let actualCallback = callback;
  if (typeof options === 'function') {
    actualCallback = options;
    actualOptions = undefined;
  }

  return originalReadFile.call(fs, pathArg, actualOptions, (err: any, data: any) => {
    if (err) {
      if (actualCallback) actualCallback(err, data);
      return;
    }
    const relPath = getRelativePath(pathArg);
    if (relPath && shouldPatch(relPath)) {
      const originalContent = typeof data === 'string' ? data : data.toString('utf8');
      const patchedContent = applyPatches(pathArg, originalContent);
      const returnData = typeof data === 'string' ? patchedContent : Buffer.from(patchedContent, 'utf8');
      if (actualCallback) actualCallback(null, returnData);
    } else {
      if (actualCallback) actualCallback(null, data);
    }
  });
} as any;

// 3. promises.readFile Hook
fs.promises.readFile = async function (this: any, pathArg: any, options?: any) {
  const result = await originalPromisesReadFile.call(fs.promises, pathArg, options);
  const relPath = getRelativePath(pathArg);
  if (relPath && shouldPatch(relPath)) {
    const originalContent = typeof result === 'string' ? result : result.toString('utf8');
    const patchedContent = applyPatches(pathArg, originalContent);
    if (typeof result === 'string') {
      return patchedContent;
    }
    return Buffer.from(patchedContent, 'utf8');
  }
  return result;
} as any;

// Make sure fs/promises named imports also point to our hooked version
promises.readFile = fs.promises.readFile;

// Keep existing express AllowedHosts and AXIOS rewrites
import express from 'express';
import axios from 'axios';

const originalUse = express.application.use;
let hostMiddlewareAdded = false;

function matchesAllowedHost(host: string, allowedPatternsStr: string): boolean {
  if (!host || !allowedPatternsStr) return false;
  const hostname = host.split(':')[0];
  
  const patterns = allowedPatternsStr.split(',').map(p => p.trim()).filter(Boolean);
  return patterns.some(pattern => {
    const regexPattern = '^' + pattern
      .replace(/\./g, '\\.')
      .replace(/\*/g, '[a-zA-Z0-9-]+') + '$';
    try {
      const regex = new RegExp(regexPattern, 'i');
      return regex.test(hostname);
    } catch (e) {
      console.error(`[Bootstrap] Invalid ALLOWED_HOST pattern "${pattern}":`, e);
      return false;
    }
  });
}

express.application.use = function (this: any, ...args: any[]) {
  if (!hostMiddlewareAdded) {
    hostMiddlewareAdded = true;
    console.log("[Bootstrap] Injecting Host rewriting middleware and headers");
    originalUse.call(this, (req: any, res: any, next: any) => {
      // Inject Cross-Origin Isolation headers required for SharedArrayBuffer / WASM pthreads
      res.setHeader('Cross-Origin-Opener-Policy', 'same-origin');
      res.setHeader('Cross-Origin-Embedder-Policy', 'require-corp');

      const host = req.headers.host || req.headers[':authority'] || '';
      const hostname = host.split(':')[0];
      
      const isLocal = hostname === 'localhost' || hostname === '127.0.0.1';
      const allowedPattern = process.env.ALLOWED_HOST;
      const isAllowed = allowedPattern && matchesAllowedHost(host, allowedPattern);

      if (isLocal || isAllowed) {
        if (req.headers.host) {
          req.headers.host = 'localhost';
        }
        if (req.headers[':authority']) {
          req.headers[':authority'] = 'localhost';
        }
      }

      next();
    });
  }
  return originalUse.apply(this, args);
};

// Helper to extract fields from Form-Data object
function getFormField(form: any, fieldName: string): string | null {
  if (!form || !Array.isArray(form._streams)) return null;
  const streams = form._streams;
  for (let i = 0; i < streams.length; i++) {
    const item = streams[i];
    if (typeof item === 'string' && item.includes(`name="${fieldName}"`)) {
      const val = streams[i + 1];
      if (typeof val === 'string') {
        return val;
      }
    }
  }
  return null;
}

// Monkeypatch axios.post to route requests based on modelId via Nginx
function patchAxiosInstance(axiosInstance: any, label: string) {
  const originalPost = axiosInstance.post;
  axiosInstance.post = function (this: any, url: string, data?: any, config?: any) {
    if (url && (url.endsWith('/transcribe') || url.includes('/transcribe'))) {
      let modelId = 'faster-whisper';
      if (data && typeof data === 'object') {
        if (data.modelId) {
          modelId = data.modelId;
        } else {
          const extracted = getFormField(data, 'modelId');
          if (extracted) {
            modelId = extracted;
          }
        }
      }
      modelId = modelId.toLowerCase().trim();
      if (modelId === 'whisper.cpp') {
        modelId = 'whisper-cpp';
      }
      url = `${url}/${modelId}`;
      console.log(`[Bootstrap] [${label}] Rewriting ASR request URL to: ${url}`);
    }
    return originalPost.call(this, url, data, config);
  };
}

patchAxiosInstance(axios, 'ESM');

try {
  const cjsAxios = require('axios');
  if (cjsAxios && cjsAxios !== axios) {
    console.log("[Bootstrap] Detected distinct CommonJS axios instance, applying patch");
    patchAxiosInstance(cjsAxios, 'CJS');
  }
} catch (err) {
  console.warn("[Bootstrap] Could not patch CJS axios instance:", err);
}

const originalListen = express.application.listen;
express.application.listen = function (this: any, port: any, ...args: any[]) {
  const targetPort = process.env.PORT ? parseInt(process.env.PORT, 10) : port;
  console.log(`[Bootstrap] Redirecting express listen from port ${port} to ${targetPort}`);
  
  let callback = args[args.length - 1];
  if (typeof callback === 'function') {
    args[args.length - 1] = function (this: any, ...cbArgs: any[]) {
      console.log(`[Bootstrap] Server is now listening on http://localhost:${targetPort}`);
      return callback.apply(this, cbArgs);
    };
  } else {
    args.push(function() {
      console.log(`[Bootstrap] Server is now listening on http://localhost:${targetPort}`);
    });
  }

  return originalListen.call(this, targetPort, ...args);
};

// Start the real stt-arena server
import('./stt-arena-design/server.ts').catch((e) => {
  console.error("Failed to load stt-arena-design server:", e);
  process.exit(1);
});
