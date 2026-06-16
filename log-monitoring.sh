#!/usr/bin/env bash
# Follow live dev-server output written by run-3041.sh (logs/vite-3041.log).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="$ROOT/logs/stt-arena-3042.log"

if [[ ! -f "$LOG_FILE" ]]; then
  echo "Log file not found: $LOG_FILE" >&2
  echo "Start the app with ./run-3042.sh first (it creates logs/stt-arena-3042.log)." >&2
  exit 1
fi

echo "Tailing $LOG_FILE (Ctrl+C to stop watching)" >&2
tail -f "$LOG_FILE"
