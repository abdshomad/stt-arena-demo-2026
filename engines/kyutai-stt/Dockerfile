FROM stt-arena-base:transformers
WORKDIR /app
COPY common/engine_common.py ./engine_common.py
COPY kyutai-stt/main.py ./main.py
EXPOSE 8027
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8027"]
