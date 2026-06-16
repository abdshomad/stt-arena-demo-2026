# Stage 1: build whisper.cpp binary with CUDA support
FROM nvidia/cuda:12.2.2-devel-ubuntu22.04 AS builder
RUN apt-get update && apt-get install -y --no-install-recommends \
    git curl build-essential cmake ca-certificates \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /build
RUN git clone --depth 1 https://github.com/ggerganov/whisper.cpp.git
WORKDIR /build/whisper.cpp
RUN cmake -B build -DGGML_CUDA=ON -DBUILD_SHARED_LIBS=ON \
    -DCMAKE_EXE_LINKER_FLAGS="-Wl,--allow-shlib-undefined" \
    -DCMAKE_SHARED_LINKER_FLAGS="-Wl,--allow-shlib-undefined" \
    -DCMAKE_INSTALL_PREFIX=/install
RUN cmake --build build --config Release -j$(nproc)
RUN cmake --install build

# Stage 2: runner — ggml models download on demand, GPU acceleration
FROM nvidia/cuda:12.2.2-runtime-ubuntu22.04
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip ffmpeg libsndfile1 ca-certificates \
    && rm -rf /var/lib/apt/lists/*
RUN pip3 install --no-cache-dir fastapi uvicorn python-multipart
WORKDIR /app
COPY --from=builder /install/ /usr/local/
RUN ldconfig
RUN ln -s /usr/local/bin/whisper-cli ./whisper-cpp
COPY common/engine_common.py ./engine_common.py
COPY whisper-cpp/main.py ./main.py
EXPOSE 8004
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8004"]
