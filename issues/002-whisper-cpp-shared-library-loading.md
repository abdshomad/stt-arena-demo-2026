# Issue 002: Whisper.cpp Shared Library Loading Failure (Exit Code 127)

## Symptoms
ASR transcription requests routed to the Whisper.cpp engine returned an error containing:
`[whisper.cpp error: Command '['./whisper-cpp', ...] returned non-zero exit status 127.]`
Running the `./whisper-cpp` binary inside the container manually returned:
`./whisper-cpp: error while loading shared libraries: libwhisper.so.1: cannot open shared object file: No such file or directory` or `libggml.so.0: cannot open shared object file`

## Root Cause
The `whisper.cpp` build configuration compiles shared libraries (`libwhisper.so*` and `libggml*.so*`) in the builder stage. While the main executable was copied to the runner stage, the shared libraries were left in the builder stage. As a result, the runner stage's dynamic linker could not locate these required shared libraries at runtime, throwing exit status 127.

## Resolution
Modified `engines/whisper-cpp/Dockerfile` to copy both the `libwhisper.so*` and `libggml*.so*` shared library files from the builder stage to `/usr/local/lib/` (a standard dynamic linker search path) and executed `ldconfig` during container build to update the linker cache:
```dockerfile
COPY --from=builder /build/whisper.cpp/build/src/libwhisper.so* /usr/local/lib/
COPY --from=builder /build/whisper.cpp/build/ggml/src/libggml*.so* /usr/local/lib/
RUN ldconfig
```
Rebuilt the `whisper-cpp-engine` image and confirmed the binary executes and transcribes successfully.
