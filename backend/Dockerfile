# syntax=docker/dockerfile:1.6

FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    HF_HOME=/root/.cache/huggingface

WORKDIR /app

# Runtime deps for pypdf / tokenizers / torch. build-essential is dropped from
# the final layer to keep the image smaller — only python wheels are used.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       curl \
       ca-certificates \
       libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY app ./app
COPY data ./data
COPY scripts ./scripts
COPY docker-entrypoint.sh ./docker-entrypoint.sh
RUN chmod +x /app/docker-entrypoint.sh

EXPOSE 8000

ENV API_HOST=0.0.0.0 \
    API_PORT=8000 \
    CHROMA_PATH=/app/data/chroma \
    OBSERVABILITY_LOG_DIR=/app/logs \
    MLFLOW_TRACKING_URI=/app/mlruns \
    CORS_ORIGINS=http://localhost:3000

VOLUME ["/app/data/chroma", "/app/logs", "/app/mlruns", "/root/.cache/huggingface"]

ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
