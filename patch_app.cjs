/**
 * Build-time patches applied to the COPY of the stt-arena-design submodule
 * inside the Docker image (the submodule working tree itself is never edited,
 * per AGENTS.md).
 *
 * Goal: make the arena REALLY use the local STT engines (backend only, since
 * frontend has native browser support now).
 *  1. server.ts: /api/engines/health proxy.
 *  2. sttService.ts: 30-minute forward timeout + honest diarization check for whisperx.
 */
const fs = require('fs');
const path = require('path');

function normalizeNewlines(str) {
  return str.replace(/\r\n/g, '\n');
}

let failures = 0;

function patchFile(relPath, label, target, replacement, { critical = true } = {}) {
  const filePath = path.join(__dirname, relPath);
  if (!fs.existsSync(filePath)) {
    console.error(`[${label}] MISSING FILE: ${relPath}`);
    if (critical) failures++;
    return;
  }
  const content = normalizeNewlines(fs.readFileSync(filePath, 'utf8'));
  if (content.includes(replacement.trim().split('\n')[0]) && !content.includes(target)) {
    console.log(`[${label}] looks already patched — skipping.`);
    return;
  }
  if (!content.includes(target)) {
    console.error(`[${label}] target string not found in ${relPath}`);
    if (critical) failures++;
    return;
  }
  fs.writeFileSync(filePath, content.replace(target, replacement));
  console.log(`[${label}] patched ${relPath}`);
}

/* ------------------------------------------------------------------ */
/* 1. server.ts — /api/engines/health proxy                           */
/* ------------------------------------------------------------------ */
patchFile(
  'server.ts',
  'engine-health-proxy',
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

/* ------------------------------------------------------------------ */
/* 2. sttService.ts — long timeout for cold on-demand CPU loads       */
/* ------------------------------------------------------------------ */
patchFile(
  'server/sttService.ts',
  'forward-timeout',
  'timeout: 30000 // 30 seconds max timeout',
  'timeout: 1800000 // 30 minutes: cold on-demand model loads on CPU are slow'
);

/* ------------------------------------------------------------------ */
/* 3. Honest diarization: whisperx-only                               */
/* ------------------------------------------------------------------ */
patchFile(
  'server/sttService.ts',
  'diarization-honest-server',
  'const supportsDiarization = modelId === "elevenlabs-stt" || modelId === "gcp-stt" || modelId === "assembly-ai" || modelId.includes("omni") || modelId.includes("diarization");',
  'const supportsDiarization = modelId.includes("whisperx");',
  { critical: false }
);

/* ------------------------------------------------------------------ */
/* 4. React state closure-bug fix in App.tsx                          */
/* ------------------------------------------------------------------ */
patchFile(
  'src/App.tsx',
  'closure-bug',
  'setArenaLogs(prev => [...prev, `[${(currentPct * 0.05).toFixed(1)}s] ${logTimeline[currentLogIndex].msg}`]);',
  'const logMsg = logTimeline[currentLogIndex]?.msg; if (logMsg) { setArenaLogs(prev => [...prev, `[${(currentPct * 0.05).toFixed(1)}s] ${logMsg}`]); }',
  { critical: false }
);

if (failures > 0) {
  console.error(`${failures} critical patch(es) failed.`);
  process.exit(1);
}
console.log('All patches applied.');
