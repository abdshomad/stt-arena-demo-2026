FROM stt-arena-base:nemo
WORKDIR /app
COPY common/engine_common.py ./engine_common.py
COPY nvidia-nemotron-speech-streaming-en/main.py ./main.py
EXPOSE 8031
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8031"]
