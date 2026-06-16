FROM stt-arena-base:whisperx
WORKDIR /app
COPY common/engine_common.py ./engine_common.py
COPY whisperx/main.py ./main.py
EXPOSE 8003
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8003"]
