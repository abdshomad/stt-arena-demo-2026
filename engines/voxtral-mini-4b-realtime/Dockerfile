FROM stt-arena-base:transformers
WORKDIR /app
COPY common/engine_common.py ./engine_common.py
COPY voxtral-mini-4b-realtime/main.py ./main.py
EXPOSE 8022
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8022"]
