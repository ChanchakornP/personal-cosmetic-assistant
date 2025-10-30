# FastAPI recommendation system
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app/recomsystem

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
 && rm -rf /var/lib/apt/lists/*

# Install dependencies first to leverage docker cache
COPY requirement.txt /app/recomsystem/requirement.txt
RUN pip install --no-cache-dir -r requirement.txt

# Copy app
COPY . /app/recomsystem

EXPOSE 8001

# Default PRODUCT_API_URL will be set via docker-compose to talk to product service
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
