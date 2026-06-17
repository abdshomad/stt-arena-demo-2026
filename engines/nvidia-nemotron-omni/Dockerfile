FROM pytorch/pytorch:2.5.1-cuda12.1-cudnn9-devel

# Install apt dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg libsndfile1 git build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies matching transformers base image
RUN pip install --no-cache-dir --extra-index-url https://download.pytorch.org/whl/cu121 \
    "torch==2.5.1+cu121" \
    "torchvision==0.20.1+cu121" \
    "transformers>=4.56" \
    accelerate \
    librosa \
    soundfile \
    sentencepiece \
    tiktoken \
    timm \
    num2words \
    fastapi \
    uvicorn \
    python-multipart \
    open-clip-torch

# Install mamba-ssm and causal-conv1d (compiling them with nvcc using no build isolation)
RUN pip install --no-cache-dir --no-build-isolation --extra-index-url https://download.pytorch.org/whl/cu121 \
    "torch==2.5.1+cu121" \
    "torchvision==0.20.1+cu121" \
    einops \
    causal-conv1d>=1.2.0 \
    mamba-ssm>=1.2.0

WORKDIR /app
COPY common/engine_common.py ./engine_common.py
COPY nvidia-nemotron-omni/main.py ./main.py
EXPOSE 8008
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8008"]
