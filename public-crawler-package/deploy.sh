#!/usr/bin/env bash
set -euo pipefail
ROOT=$(pwd)
echo "Deploy script starting in $ROOT"
docker compose -f docker-compose.prod.yml build --pull
mkdir -p ./certbot/www ./certbot/conf ./data/sqlite ./backups
docker compose -f docker-compose.prod.yml up -d nginx
echo "Obtain certs using certbot command (manual step)"
docker compose -f docker-compose.prod.yml up -d
echo "Services started."
