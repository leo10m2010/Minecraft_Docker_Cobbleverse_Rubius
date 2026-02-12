#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
BACKUP_ROOT="$ROOT_DIR/backups/pre-update"
COMPOSE_FILE="${COMPOSE_FILE:-$ROOT_DIR/docker-compose.yml}"

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "Comando requerido no encontrado: $1"
    exit 1
  }
}

STAMP="$(date +%Y%m%d-%H%M%S)"
FAILED_DIR="$ROOT_DIR/data.failed.$STAMP"
DATA_MOVED=0

on_error() {
  echo "Error durante rollback."
  if [ "$DATA_MOVED" -eq 1 ] && [ ! -d "$ROOT_DIR/data" ] && [ -d "$FAILED_DIR" ]; then
    echo "Intentando restaurar el estado previo desde: $FAILED_DIR"
    mv "$FAILED_DIR" "$ROOT_DIR/data" || true
  fi
}

trap on_error ERR
require_cmd docker

if [ ! -d "$BACKUP_ROOT" ]; then
  echo "No existe la carpeta de backups: $BACKUP_ROOT"
  exit 1
fi

if [ "${1:-}" != "" ]; then
  RESTORE_DIR="$BACKUP_ROOT/$1"
else
  shopt -s nullglob
  BACKUPS=("$BACKUP_ROOT"/*)
  shopt -u nullglob

  if [ "${#BACKUPS[@]}" -eq 0 ]; then
    echo "No hay backups disponibles en: $BACKUP_ROOT"
    exit 1
  fi

  IFS=$'\n' SORTED_BACKUPS=($(printf '%s\n' "${BACKUPS[@]}" | sort))
  LAST_INDEX=$((${#SORTED_BACKUPS[@]} - 1))
  RESTORE_DIR="${SORTED_BACKUPS[$LAST_INDEX]}"
fi

if [ ! -d "$RESTORE_DIR" ] || [ ! -d "$RESTORE_DIR/data" ]; then
  echo "Backup invalido o no encontrado: $RESTORE_DIR"
  exit 1
fi

echo "[1/5] Deteniendo stack..."
docker compose -f "$COMPOSE_FILE" down

echo "[2/5] Conservando estado actual en: $FAILED_DIR"
if [ -d "$ROOT_DIR/data" ]; then
  mv "$ROOT_DIR/data" "$FAILED_DIR"
  DATA_MOVED=1
else
  echo "No existe $ROOT_DIR/data. Se continua con restauracion directa."
fi

echo "[3/5] Restaurando backup: $RESTORE_DIR"
mkdir -p "$ROOT_DIR/data"
cp -a "$RESTORE_DIR/data/." "$ROOT_DIR/data"

if [ -f "$RESTORE_DIR/docker-compose.yml" ]; then
  cp -f "$RESTORE_DIR/docker-compose.yml" "$ROOT_DIR/docker-compose.yml"
fi
if [ -f "$RESTORE_DIR/.env" ]; then
  cp -f "$RESTORE_DIR/.env" "$ROOT_DIR/.env"
fi

echo "[4/5] Levantando stack restaurado..."
docker compose -f "$COMPOSE_FILE" up -d

echo "[5/5] Rollback completado"
echo "Estado previo al rollback guardado en: $FAILED_DIR"
echo "Verifica logs con: docker logs -f mc-evolution-16gb"
