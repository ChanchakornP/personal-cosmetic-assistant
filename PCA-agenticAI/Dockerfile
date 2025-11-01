# FastAPI recommendation system with LangChain AgenticAI
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app/PCA-agenticAI

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
 && rm -rf /var/lib/apt/lists/*

# Install dependencies first to leverage docker cache
COPY requirements.txt /app/PCA-agenticAI/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY . /app/PCA-agenticAI

EXPOSE 8001

# Default configuration will be set via docker-compose or .env file
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]

