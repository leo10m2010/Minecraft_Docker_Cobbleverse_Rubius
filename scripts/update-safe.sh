#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
BACKUP_ROOT="$ROOT_DIR/backups/pre-update"
STAMP="$(date +%Y%m%d-%H%M%S)"
TARGET="$BACKUP_ROOT/$STAMP"

echo "[1/6] Preparando rutas..."
mkdir -p "$TARGET"

echo "[2/6] Deteniendo stack..."
docker compose -f "$ROOT_DIR/docker-compose.yml" down

echo "[3/6] Respaldando estado actual..."
mkdir -p "$TARGET"
cp -a "$ROOT_DIR/data" "$TARGET/data"
cp -a "$ROOT_DIR/docker-compose.yml" "$TARGET/docker-compose.yml"

echo "[4/6] Actualizando imagen..."
docker compose -f "$ROOT_DIR/docker-compose.yml" pull

echo "[5/6] Levantando version actualizada..."
docker compose -f "$ROOT_DIR/docker-compose.yml" up -d

echo "[6/6] Listo. Backup creado en: $TARGET"
echo "Verifica logs con: docker logs -f mc-evolution-16gb"
