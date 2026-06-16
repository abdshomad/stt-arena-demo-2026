# Issue: Meta Omnilingual ASR torchaudio libcudart.so.13 load failure

## Symptoms
When triggering a model load for the Meta Omnilingual engine (`meta-omnilingual-asr`), the engine backend returned a `500 Internal Server Error` with the following traceback in the container logs:
```
  File "/usr/local/lib/python3.12/site-packages/torchaudio/_extension/utils.py", line 56, in _load_lib
    torch.ops.load_library(paths[0])
  File "/usr/local/lib/python3.12/site-packages/torch/_ops.py", line 1478, in load_library
    ctypes.CDLL(path)
  File "/usr/local/lib/python3.12/ctypes/__init__.py", line 379, in __init__
    self._handle = _dlopen(self._name, mode)
OSError: libcudart.so.13: cannot open shared object file: No such file or directory
```

## Root Cause
- The base image `stt-arena-base:omnilingual` was installing `torch` and `torchaudio` from `https://download.pytorch.org/whl/cu121`, which resolved to PyTorch 2.5.1 and torchaudio 2.5.1.
- However, when `pip install omnilingual-asr` was executed, its dependency resolution pulled `torch 2.8.0` (with cu128 dependencies) and a mismatched `torchaudio 2.11.0` package from the standard PyPI index instead of the PyTorch CUDA index.
- `torchaudio 2.11.0` was built against a future CUDA 13.x toolchain, resulting in it looking for the non-existent `libcudart.so.13` library on host machines with CUDA 12.8.

## Resolution
- Modified `engines/common/docker/Dockerfile.omnilingual` to explicitly run a post-install step:
  ```dockerfile
  && pip install --no-cache-dir torchaudio==2.8.0+cu128 --index-url https://download.pytorch.org/whl/cu128
  ```
- This downgrades/aligns the `torchaudio` version to match the installed `torch 2.8.0` version and configures it to run against CUDA 12.8 directly, resolving the `libcudart.so.13` dynamic loading issue.
- Successfully verified that the Meta Omnilingual ASR engine now loads and runs on GPU 1.
