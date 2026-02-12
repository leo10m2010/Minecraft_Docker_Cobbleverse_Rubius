#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
BACKUP_ROOT="$ROOT_DIR/backups/pre-update"
STAMP="$(date +%Y%m%d-%H%M%S)"
TARGET="$BACKUP_ROOT/$STAMP"
COMPOSE_FILE="${COMPOSE_FILE:-$ROOT_DIR/docker-compose.yml}"
RETENTION_DAYS="${PRE_UPDATE_RETENTION_DAYS:-14}"

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "Comando requerido no encontrado: $1"
    exit 1
  }
}

on_error() {
  echo "Error durante update-safe. El stack queda detenido para revision manual."
  echo "Si necesitas volver al estado anterior: ./scripts/rollback-last-update.sh $STAMP"
}

trap on_error ERR
require_cmd docker

echo "[1/6] Preparando rutas..."
mkdir -p "$TARGET"

echo "[2/6] Deteniendo stack..."
docker compose -f "$COMPOSE_FILE" down

echo "[3/6] Respaldando estado actual..."
if [ -d "$ROOT_DIR/data" ]; then
  cp -a "$ROOT_DIR/data" "$TARGET/data"
else
  echo "No existe $ROOT_DIR/data. Se crea backup vacio para data."
  mkdir -p "$TARGET/data"
fi
cp -a "$ROOT_DIR/docker-compose.yml" "$TARGET/docker-compose.yml"
if [ -f "$ROOT_DIR/.env" ]; then
  cp -a "$ROOT_DIR/.env" "$TARGET/.env"
fi

echo "[4/6] Actualizando imagen..."
docker compose -f "$COMPOSE_FILE" pull

echo "[5/6] Levantando version actualizada..."
docker compose -f "$COMPOSE_FILE" up -d

if [[ "$RETENTION_DAYS" =~ ^[0-9]+$ ]] && [ "$RETENTION_DAYS" -gt 0 ]; then
  find "$BACKUP_ROOT" -mindepth 1 -maxdepth 1 -type d -mtime "+$RETENTION_DAYS" -exec rm -rf {} +
fi

echo "[6/6] Listo. Backup creado en: $TARGET"
echo "Verifica logs con: docker logs -f mc-evolution-16gb"
