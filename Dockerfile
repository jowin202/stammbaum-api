
FROM public.ecr.aws/docker/library/python:3.12-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends postgresql-client && \
    rm -rf /var/lib/apt/lists/*
    
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

CMD uvicorn main:app --host 0.0.0.0 --port 8000 --log-level debug --reload

