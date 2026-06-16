FROM stt-arena-base:nemo
WORKDIR /app
COPY common/engine_common.py ./engine_common.py
COPY nvidia-canary-180m-flash/main.py ./main.py
EXPOSE 8033
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8033"]
