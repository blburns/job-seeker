FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev && rm -rf /var/lib/apt/lists/*

COPY requirements/requirements.txt requirements/requirements-jobs.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements-jobs.txt

COPY . .

ENV FLASK_APP=run.py
EXPOSE 5000

CMD ["python", "run.py"]
