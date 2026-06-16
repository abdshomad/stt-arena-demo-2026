FROM stt-arena-base:transformers
WORKDIR /app
COPY common/engine_common.py ./engine_common.py
COPY indonesian-nlp-wav2vec2-indonesian-javanese-sundanese/main.py ./main.py
EXPOSE 8015
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8015"]
