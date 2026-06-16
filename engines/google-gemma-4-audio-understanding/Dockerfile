FROM stt-arena-base:transformers
WORKDIR /app
COPY common/engine_common.py ./engine_common.py
COPY google-gemma-4-audio-understanding/main.py ./main.py
EXPOSE 8011
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8011"]
