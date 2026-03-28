FROM python:3.11-slim

WORKDIR /app

# Install dependencies first (cached layer — only rebuilds when requirements.txt changes)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code into the 'api' package directory
RUN mkdir -p api
COPY . api/
RUN touch api/__init__.py

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
