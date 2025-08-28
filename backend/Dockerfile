FROM python:3.8-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_PORT=8003

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        pkg-config \
        libmariadb-dev \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r /app/requirements.txt

COPY app /app/app

EXPOSE 8003

ENTRYPOINT ["bash", "-lc", "python -m app.seed || echo '[WARN] seed saltato'; exec uvicorn app.main:app --host 0.0.0.0 --port ${APP_PORT:-8000}"]