FROM stt-arena-base:whisper
WORKDIR /app
COPY common/engine_common.py ./engine_common.py
COPY whisper/main.py ./main.py
EXPOSE 8001
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
