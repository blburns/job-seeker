FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev \
    libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 \
    libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm1 libasound2 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements/requirements.txt requirements/requirements-jobs.txt requirements/requirements-celery.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements-jobs.txt -r requirements-celery.txt
RUN playwright install chromium || true

COPY . .

ENV FLASK_APP=run.py
EXPOSE 5000

CMD ["python", "run.py"]
