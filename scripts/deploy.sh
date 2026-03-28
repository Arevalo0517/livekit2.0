#!/usr/bin/env bash
set -euo pipefail

APP_DIR="/opt/voiceai"

echo "=== Changing to app directory ==="
cd "$APP_DIR"

echo "=== Pulling latest code ==="
git pull origin main

echo "=== Building and restarting services ==="
docker compose -f "$APP_DIR/docker-compose.yml" pull
docker compose -f "$APP_DIR/docker-compose.yml" up -d --build

echo "=== Checking service health ==="
sleep 5
docker compose -f "$APP_DIR/docker-compose.yml" ps

echo "=== Deploy complete ==="
