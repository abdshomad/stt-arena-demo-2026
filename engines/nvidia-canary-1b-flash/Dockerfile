FROM stt-arena-base:nemo
WORKDIR /app
COPY common/engine_common.py ./engine_common.py
COPY nvidia-canary-1b-flash/main.py ./main.py
EXPOSE 8037
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8037"]
