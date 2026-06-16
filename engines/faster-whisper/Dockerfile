FROM stt-arena-base:ct2
WORKDIR /app
COPY common/engine_common.py ./engine_common.py
COPY faster-whisper/main.py ./main.py
EXPOSE 8002
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"]
