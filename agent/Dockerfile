FROM python:3.11-slim

WORKDIR /app

# Install dependencies first (Docker layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# LiveKit Agents CLI: 'start' subcommand runs the worker
CMD ["python", "worker.py", "start"]
