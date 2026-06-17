# Issue: Move Engine Cache to Local Server Cache

## Symptoms
The repository directory was accumulating over 210 GB of downloaded engine models and caches inside `./engines/cache/`, cluttering the project workspace and causing potential sync/storage issues.

## Root Cause
In `docker-compose.yml`, the engine services mapped their `/root/.cache` volumes to `./engines/cache` on the host, saving all HuggingFace and other model weights inside the repository.

## Resolution
1. Modified `docker-compose.yml` to change the volume mapping to `/home/aiserver/.cache:/root/.cache`.
2. Updated `README.md` and `assumptions/004-on-demand-loading-and-resources.md` references.
3. Synced the existing cache files from `./engines/cache` to the local server cache `/home/aiserver/.cache` using an Alpine Docker container running `rsync -aH` to preserve all files and hard links.
4. Cleaned up `./engines/cache` after sync.
5. Recreated containers with `docker compose down` and `docker compose up -d` to load cache from the new location.
6. Verified with end-to-end engine tests.
