FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    TEMP_DIR=/tmp/neuroarchive

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg ca-certificates curl unzip \
    && rm -rf /var/lib/apt/lists/*

# yt-dlp shells out to Deno for YouTube signature/nsig deciphering
RUN curl -fsSL https://deno.land/install.sh | DENO_INSTALL=/usr/local sh -s -- -y \
    && chmod +x /usr/local/bin/deno

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app ./app

RUN mkdir -p /tmp/neuroarchive

# Run RQ worker against the neuroarchive queue
CMD ["rq", "worker", "neuroarchive", "--url", "redis://redis:6379/0", "--path", "/app"]
