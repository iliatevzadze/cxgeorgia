FROM python:3.12-slim

RUN groupadd --system appuser && useradd --system --gid appuser --home-dir /app appuser

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY pyproject.toml README.md ./
COPY worker ./worker

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir . && \
    chown -R appuser:appuser /app

USER appuser

CMD ["celery", "-A", "worker.celery_app:celery_app", "worker", "--loglevel=INFO"]
