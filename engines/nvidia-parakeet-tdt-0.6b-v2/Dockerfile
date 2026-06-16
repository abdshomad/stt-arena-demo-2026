FROM stt-arena-base:nemo
WORKDIR /app
COPY common/engine_common.py ./engine_common.py
COPY nvidia-parakeet-tdt-0.6b-v2/main.py ./main.py
EXPOSE 8036
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8036"]
