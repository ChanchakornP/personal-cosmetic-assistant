# FastAPI product service
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app/product

# System deps (curl for health/debug), build base in case of wheels
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# Install dependencies first to leverage docker cache
COPY requirement.txt /app/product/requirement.txt
RUN pip install --no-cache-dir -r requirement.txt

# Copy app
COPY . /app/product

EXPOSE 8000

# Note: This code expects very specific env var names (URLs as keys). We can pass them via docker-compose.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
