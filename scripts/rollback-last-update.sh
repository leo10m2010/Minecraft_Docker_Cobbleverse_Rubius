#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
BACKUP_ROOT="$ROOT_DIR/backups/pre-update"

if [ ! -d "$BACKUP_ROOT" ]; then
  echo "No existe la carpeta de backups: $BACKUP_ROOT"
  exit 1
fi

if [ "${1:-}" != "" ]; then
  RESTORE_DIR="$BACKUP_ROOT/$1"
else
  RESTORE_DIR="$(ls -1d "$BACKUP_ROOT"/* 2>/dev/null | tail -n 1)"
fi

if [ ! -d "$RESTORE_DIR" ] || [ ! -d "$RESTORE_DIR/data" ]; then
  echo "Backup invalido o no encontrado: $RESTORE_DIR"
  exit 1
fi

STAMP="$(date +%Y%m%d-%H%M%S)"
FAILED_DIR="$ROOT_DIR/data.failed.$STAMP"

echo "[1/5] Deteniendo stack..."
docker compose -f "$ROOT_DIR/docker-compose.yml" down

echo "[2/5] Conservando estado actual en: $FAILED_DIR"
mv "$ROOT_DIR/data" "$FAILED_DIR"

echo "[3/5] Restaurando backup: $RESTORE_DIR"
cp -a "$RESTORE_DIR/data" "$ROOT_DIR/data"

if [ -f "$RESTORE_DIR/docker-compose.yml" ]; then
  cp -f "$RESTORE_DIR/docker-compose.yml" "$ROOT_DIR/docker-compose.yml"
fi

echo "[4/5] Levantando stack restaurado..."
docker compose -f "$ROOT_DIR/docker-compose.yml" up -d

echo "[5/5] Rollback completado"
echo "Estado previo al rollback guardado en: $FAILED_DIR"
echo "Verifica logs con: docker logs -f mc-evolution-16gb"
