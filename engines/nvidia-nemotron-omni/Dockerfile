FROM stt-arena-base:transformers
WORKDIR /app
COPY common/engine_common.py ./engine_common.py
COPY nvidia-nemotron-omni/main.py ./main.py
EXPOSE 8008
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8008"]
