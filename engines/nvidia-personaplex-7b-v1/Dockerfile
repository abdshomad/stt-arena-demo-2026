FROM stt-arena-base:transformers
WORKDIR /app
COPY common/engine_common.py ./engine_common.py
COPY nvidia-personaplex-7b-v1/main.py ./main.py
EXPOSE 8023
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8023"]
