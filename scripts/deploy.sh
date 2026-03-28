#!/usr/bin/env bash
set -euo pipefail

echo "=== Pulling latest code ==="
git pull origin main

echo "=== Building and restarting services ==="
docker compose pull
docker compose up -d --build

echo "=== Checking service health ==="
sleep 5
docker compose ps

echo "=== Deploy complete ==="
