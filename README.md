# stt-arena-design-demo-2026

Wrapper scripts drive the bundled [Git submodule app](stt-arena-design).

## Run on port 3042

1. **Port and public config** live in [`.env`](.env) (`PORT=3042`, `APP_URL`).
2. **API keys** — copy [`.secrets.example`](.secrets.example) to `.secrets` and set `GEMINI_API_KEY` (and any other keys). `.secrets` is gitignored.
3. From this directory:

```bash
./run-3042.sh
```

This frees anything already listening on `PORT`, raises the open‑file descriptor limit where allowed, starts the bootstrap server in the background, and writes `logs/stt-arena-3042.pid`. Dependencies install via `./install.sh` when `node_modules` is missing, or with `REINSTALL=1 ./run-3042.sh`.

Logs append to `logs/stt-arena-3042.log`. In another terminal:

```bash
./log-monitoring.sh
```

Requires Node/npm.

## Run with Docker Compose

If you prefer to run the application in a Docker container:

1. Make sure your `.env` and `.secrets` files are created from the examples.
   Optional keys in `.secrets` unlock the API-backed engines and gated models:
   `OPENAI_API_KEY`, `GEMINI_API_KEY`, `AZURE_SPEECH_KEY`+`AZURE_SPEECH_REGION`,
   `HF_TOKEN` (gated Gemma 3n, whisperx diarization). Engines without their key
   show as gray/N/A in the UI.
2. Build the shared engine base images once (also after changing `engines/common/docker/*`):

```bash
./engines/build-bases.sh
```

3. Build and start the containers:

```bash
docker compose up --build -d
```

Engines load their real models **on demand** at the first transcription request
(first call downloads weights into `engines/cache/` and may take minutes); idle
models unload automatically after 10 minutes. See `assumptions/` for all design
decisions.

The container will build the frontend assets, compile the backend Express server, and start it, exposing the service on `http://localhost:3042` (mapping host port 3042 to container port 3000).

To view logs:

```bash
docker compose logs -f
```

To stop the container:

```bash
docker compose down
```