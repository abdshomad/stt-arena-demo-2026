#!/usr/bin/env bash
set -euo pipefail
R="$(cd "$(dirname "$0")" && pwd)"; cd "$R"; ulimit -n 1048576 2>/dev/null||ulimit -n 65536 2>/dev/null||true
set -a; [[ -f .env ]]&&source .env; [[ -f .secrets ]]&&source .secrets; set +a
P="${PORT:-3042}"; A="$R/stt-arena-design"; L="$R/logs/stt-arena-3042.log"
if command -v fuser >/dev/null 2>&1;then fuser -k "${P}/tcp" >/dev/null 2>&1||true; fi
command -v lsof >/dev/null&&lsof -t -i:"${P}" -sTCP:LISTEN | xargs -r kill 2>/dev/null || true
[[ -d "$A/node_modules" && -z "${REINSTALL:-}" ]]||"$R/install.sh"
mkdir -p "$R/logs"; cd "$A"; setsid env NODE_PATH="node_modules" PORT="$P" npx tsx "$R/bootstrap.ts" >>"$L" 2>&1 & echo $! >"$R/logs/stt-arena-3042.pid"; cd "$R"; echo "PID $(<"$R/logs/stt-arena-3042.pid") log $L"

