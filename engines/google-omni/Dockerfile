FROM stt-arena-base:api
WORKDIR /app
COPY common/engine_common.py ./engine_common.py
COPY google-omni/main.py ./main.py
EXPOSE 8018
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8018"]
