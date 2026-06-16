#!/usr/bin/env bash
# Build the shared base images used by the engine Dockerfiles.
# Run this once before `docker compose build` (and after changing common/docker/*).
set -euo pipefail
cd "$(dirname "$0")"

for variant in api whisper ct2 whisperx transformers nemo omnilingual; do
  echo "==> Building stt-arena-base:${variant}"
  docker build -t "stt-arena-base:${variant}" -f "common/docker/Dockerfile.${variant}" common/docker/
done
echo "All base images built."
