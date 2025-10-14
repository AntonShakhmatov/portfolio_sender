FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential git curl \
    chromium \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 libatk1.0-0 \
    libc6 libdrm2 libgbm1 \
    libgtk-3-0 \
    libnspr4 libnss3 \
    libx11-6 libxcb1 libxcomposite1 libxcursor1 libxdamage1 \
    libxext6 libxfixes3 libxi6 libxrandr2 libxrender1 libxshmfence1 \
    libxss1 libxtst6 \
    libpq-dev \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*


COPY embedding/server/requirements.txt .
RUN python -m pip install --no-cache-dir -r requirements.txt

COPY embedding/server/ .

EXPOSE 5005
# важно: один процесс — API
CMD ["sh", "-lc", "python embeddings_api.py"]