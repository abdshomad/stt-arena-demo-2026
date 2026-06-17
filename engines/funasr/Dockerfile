FROM stt-arena-base:transformers
RUN pip install --no-cache-dir funasr modelscope
WORKDIR /app
COPY common/engine_common.py ./engine_common.py
COPY funasr/main.py ./main.py
EXPOSE 8040
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8040"]
