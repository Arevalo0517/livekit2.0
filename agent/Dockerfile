FROM python:3.11-slim

WORKDIR /app

# Install dependencies first (Docker layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code into the 'agent' package directory
RUN mkdir -p agent
COPY . agent/
RUN touch agent/__init__.py

# LiveKit Agents CLI: 'start' subcommand runs the worker
CMD ["python", "-m", "agent.worker", "start"]
