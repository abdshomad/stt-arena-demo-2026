# Stage 1: Build virtual environment
FROM python:3.11-slim AS builder

RUN pip install --no-cache-dir uv

WORKDIR /app
RUN uv venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN uv pip install --no-cache fastapi uvicorn python-multipart httpx

# Stage 2: Final minimal runner
FROM python:3.11-slim

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app
COPY router/main.py .

EXPOSE 5000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5000"]
