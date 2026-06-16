# Issue 013: Whisper.cpp CUDA Shared Library Loading Failure (Exit Code 127)

## Symptoms
After compiling the `whisper.cpp` engine with CUDA acceleration (`GGML_CUDA=ON`), running the `./whisper-cpp` binary inside the `whisper-cpp-engine` container failed with:
`./whisper-cpp: error while loading shared libraries: libggml-cuda.so.0: cannot open shared object file: No such file or directory`

## Root Cause
When compiling with `GGML_CUDA=ON`, CMake compiles a CUDA-specific shared library backend named `libggml-cuda.so.0`. Due to the subdirectory structure, this library is placed under `build/ggml/src/ggml-cuda/`. 
The manual copy instruction in the original Dockerfile:
`COPY --from=builder /build/whisper.cpp/build/ggml/src/libggml*.so* /usr/local/lib/`
only matched files directly under the `build/ggml/src/` folder, failing to recursively copy sub-directories and thus leaving the CUDA shared library backend behind in the builder stage.

## Resolution
Refactored `engines/whisper-cpp/Dockerfile` to use the standard and robust CMake installation prefix workflow:
1. Specified `-DCMAKE_INSTALL_PREFIX=/install` in the `cmake -B build` configuration step.
2. Ran `cmake --install build` in the builder stage to let CMake install all binaries and shared libraries (including `libggml-cuda.so.0`) automatically and cleanly under `/install/`.
3. Updated the runner stage to copy the entire `/install/` folder to `/usr/local/`, automatically placing the binary into `/usr/local/bin/whisper-cli` and all library versions into `/usr/local/lib/` (or `/usr/local/lib64/`).
4. Ran `ldconfig` to register the path, and created a symlink `./whisper-cpp` pointing to `/usr/local/bin/whisper-cli` to preserve compatibility with the engine's python server script.

Rebuilt the container image and confirmed `whisper-cli` starts up with full CUDA capabilities, detects GPU device 0, and transcribes successfully.
