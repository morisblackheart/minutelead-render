FROM python:3.11-slim

# cairosvg needs the cairo shared library at runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
    libcairo2 \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

ENV PORT=8000
CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT}"]
