# Stage 1: build parakeet.cpp binary with CUDA support
FROM nvidia/cuda:12.2.2-devel-ubuntu22.04 AS builder
RUN apt-get update && apt-get install -y --no-install-recommends \
    git curl build-essential cmake ca-certificates \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /build
RUN git clone https://github.com/mudler/parakeet.cpp.git
WORKDIR /build/parakeet.cpp
RUN git submodule update --init --recursive
RUN cmake -B build -DPARAKEET_BUILD_CLI=ON -DPARAKEET_GGML_CUDA=ON -DPARAKEET_SHARED=OFF \
    -DCMAKE_EXE_LINKER_FLAGS="-Wl,--allow-shlib-undefined" \
    -DCMAKE_SHARED_LINKER_FLAGS="-Wl,--allow-shlib-undefined" \
    -DCMAKE_BUILD_TYPE=Release
RUN cmake --build build --config Release -j$(nproc)
RUN mkdir -p /build/libs && find build -name "*.so*" -exec cp -d {} /build/libs/ \;

# Stage 2: runner — ggml models download on demand, GPU acceleration
FROM nvidia/cuda:12.2.2-runtime-ubuntu22.04
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip ffmpeg libsndfile1 ca-certificates \
    && rm -rf /var/lib/apt/lists/*
RUN pip3 install --no-cache-dir fastapi uvicorn python-multipart httpx
WORKDIR /app
COPY --from=builder /build/libs/ /usr/local/lib/
RUN ldconfig
COPY --from=builder /build/parakeet.cpp/build/examples/cli/parakeet-cli ./parakeet-cli
COPY common/engine_common.py ./engine_common.py
COPY parakeet-cpp/main.py ./main.py
EXPOSE 8041
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8041"]
