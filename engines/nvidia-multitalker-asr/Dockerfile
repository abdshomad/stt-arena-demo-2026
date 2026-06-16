FROM stt-arena-base:nemo
WORKDIR /app
COPY common/engine_common.py ./engine_common.py
COPY nvidia-multitalker-asr/main.py ./main.py
EXPOSE 8026
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8026"]
