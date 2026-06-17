# Issue: parakeet.cpp CUDA linking error in Docker build

## Symptoms
When compiling `parakeet.cpp` inside the builder stage of the Docker build with `PARAKEET_GGML_CUDA=ON`, the linking stage of `parakeet-cli` failed with:
```
/usr/bin/ld: warning: libcuda.so.1, needed by ../../third_party/ggml/src/ggml-cuda/libggml-cuda.so.0.13.0, not found (try using -rpath or -rpath-link)
/usr/bin/ld: ../../third_party/ggml/src/ggml-cuda/libggml-cuda.so.0.13.0: undefined reference to `cuMemCreate'
...
collect2: error: ld returned 1 exit status
```

## Root Cause
The `nvidia/cuda:devel` build environment does not expose the host's GPU driver library (`libcuda.so.1`) by default during `docker build`. Since the compiler attempts to link `parakeet-cli` against `libggml-cuda.so`, which has a dependency on `libcuda.so.1`, the linker raises errors for the undefined driver symbols.

## Resolution
Added `-DCMAKE_EXE_LINKER_FLAGS="-Wl,--allow-shlib-undefined"` and `-DCMAKE_SHARED_LINKER_FLAGS="-Wl,--allow-shlib-undefined"` to the `cmake` invocation in `engines/parakeet-cpp/Dockerfile`. This instructs the linker to ignore undefined symbols in shared library dependencies during the build, since the full runtime environment on the host will have the CUDA driver libraries loaded.
