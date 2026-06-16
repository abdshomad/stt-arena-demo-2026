FROM stt-arena-base:omnilingual
WORKDIR /app
COPY common/engine_common.py ./engine_common.py
COPY meta-omnilingual/main.py ./main.py
EXPOSE 8005
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8005"]
