FROM stt-arena-base:ct2
WORKDIR /app
COPY common/engine_common.py ./engine_common.py
COPY cahya-faster-whisper-medium-id/main.py ./main.py
EXPOSE 8014
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8014"]
