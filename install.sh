#!/usr/bin/env bash
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)/stt-arena-design"
npm install --legacy-peer-deps --prefix "$DIR"
exec npm install --no-save --legacy-peer-deps --prefix "$DIR" react-is
