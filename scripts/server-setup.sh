#!/usr/bin/env bash
set -euo pipefail

echo "=== Updating system packages ==="
sudo apt-get update && sudo apt-get upgrade -y

echo "=== Installing Docker ==="
sudo apt-get install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

echo "=== Adding ubuntu user to docker group ==="
sudo usermod -aG docker ubuntu
newgrp docker

echo "=== Installing Certbot ==="
sudo apt-get install -y certbot python3-certbot-nginx

echo "=== Installing Git ==="
sudo apt-get install -y git

echo "=== Creating app directory ==="
sudo mkdir -p /opt/voiceai
sudo chown ubuntu:ubuntu /opt/voiceai

echo "=== Done! Log out and log back in for docker group to take effect ==="
