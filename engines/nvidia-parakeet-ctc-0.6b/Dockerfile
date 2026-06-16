FROM stt-arena-base:nemo
WORKDIR /app
COPY common/engine_common.py ./engine_common.py
COPY nvidia-parakeet-ctc-0.6b/main.py ./main.py
EXPOSE 8034
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8034"]
