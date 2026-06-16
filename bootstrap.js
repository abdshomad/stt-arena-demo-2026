import { createRequire } from 'module';
const require = createRequire(import.meta.url);

import express from 'express';
import axios from 'axios';

// Inject Host header rewriting middleware to bypass Vite's allowedHosts check
// without editing the git submodule config files.
const originalUse = express.application.use;
let hostMiddlewareAdded = false;

function matchesAllowedHost(host, allowedPatternsStr) {
  if (!host || !allowedPatternsStr) return false;
  const hostname = host.split(':')[0];
  
  const patterns = allowedPatternsStr.split(',').map(p => p.trim()).filter(Boolean);
  return patterns.some(pattern => {
    // Convert wildcard pattern to RegExp
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

express.application.use = function (...args) {
  if (!hostMiddlewareAdded) {
    hostMiddlewareAdded = true;
    console.log("[Bootstrap] Injecting Host rewriting middleware to bypass allowedHosts check");
    originalUse.call(this, (req, res, next) => {
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
function getFormField(form, fieldName) {
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
function patchAxiosInstance(axiosInstance, label) {
  const originalPost = axiosInstance.post;
  axiosInstance.post = function (url, data, config) {
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
      // Normalize modelId for URL routing path
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
express.application.listen = function (port, ...args) {
  const targetPort = process.env.PORT ? parseInt(process.env.PORT, 10) : port;
  console.log(`[Bootstrap] Redirecting express listen from port ${port} to ${targetPort}`);
  
  // Wrap or modify the callback if provided, to log the correct port
  let callback = args[args.length - 1];
  if (typeof callback === 'function') {
    args[args.length - 1] = function (...cbArgs) {
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

import('./dist/server.cjs').catch((e) => {
  console.error("Failed to load stt-arena-design server:", e);
  process.exit(1);
});
