FROM stt-arena-base:nemo
WORKDIR /app
COPY common/engine_common.py ./engine_common.py
COPY nvidia-parakeet-rnnt-1.1b/main.py ./main.py
EXPOSE 8035
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8035"]
