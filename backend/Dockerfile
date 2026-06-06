FROM python:3.11-slim

WORKDIR /app

# System dependencies for ChromaDB and PDF
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc libpq-dev libmupdf-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p uploads/policies chroma_db

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
