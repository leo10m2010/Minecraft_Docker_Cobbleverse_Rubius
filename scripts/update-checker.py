#!/usr/bin/env python3
import json
import os
import socket
import struct
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib import parse, request


def env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        value = int(raw)
        return value
    except ValueError:
        return default


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def log(message: str) -> None:
    if CONFIG["notify_log"]:
        print(f"[{now_iso()}] [update-checker] {message}", flush=True)


def load_json(path: Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return default


def save_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")


def fetch_latest_release(project_slug: str, loader: str, game_version: str):
    query = parse.urlencode(
        {
            "loaders": json.dumps([loader]),
            "game_versions": json.dumps([game_version]),
        }
    )
    url = f"https://api.modrinth.com/v2/project/{project_slug}/version?{query}"
    req = request.Request(url, headers={"User-Agent": "cobbleverse-update-checker/1.0"})
    with request.urlopen(req, timeout=20) as response:
        payload = json.loads(response.read().decode("utf-8"))

    releases = [v for v in payload if v.get("version_type") == "release"]
    candidates = releases if releases else payload
    if not candidates:
        raise RuntimeError("No se encontraron versiones en Modrinth")

    candidates.sort(key=lambda item: item.get("date_published", ""), reverse=True)
    latest = candidates[0]
    return {
        "id": latest.get("id", ""),
        "name": latest.get("name", ""),
        "version_number": latest.get("version_number", ""),
        "date_published": latest.get("date_published", ""),
        "version_type": latest.get("version_type", ""),
    }


def read_local_manifest(path: Path):
    manifest = load_json(path, {})
    return {
        "project_slug": manifest.get("projectSlug", "cobbleverse"),
        "version_id": manifest.get("versionId", ""),
    }


def post_discord(content: str) -> None:
    webhook = CONFIG["discord_webhook"]
    if not webhook:
        log("Discord activado pero UPDATE_NOTIFY_DISCORD_WEBHOOK esta vacio")
        return

    body = json.dumps({"content": content}).encode("utf-8")
    req = request.Request(
        webhook,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with request.urlopen(req, timeout=15):
        pass


def _rcon_send(sock: socket.socket, req_id: int, packet_type: int, payload: str) -> None:
    data = payload.encode("utf-8")
    packet = struct.pack("<iii", len(data) + 10, req_id, packet_type) + data + b"\x00\x00"
    sock.sendall(packet)


def _rcon_read(sock: socket.socket):
    header = sock.recv(4)
    if len(header) < 4:
        raise RuntimeError("RCON header incompleto")
    length = struct.unpack("<i", header)[0]
    payload = b""
    while len(payload) < length:
        chunk = sock.recv(length - len(payload))
        if not chunk:
            break
        payload += chunk
    if len(payload) < 8:
        raise RuntimeError("RCON payload incompleto")
    req_id, packet_type = struct.unpack("<ii", payload[:8])
    body = payload[8:-2].decode("utf-8", errors="replace")
    return req_id, packet_type, body


def send_minecraft_message(text: str) -> None:
    if not CONFIG["rcon_password"]:
        log("Notificacion Minecraft activada pero RCON_PASSWORD esta vacio")
        return

    host = CONFIG["rcon_host"]
    port = CONFIG["rcon_port"]
    command = f'/tellraw @a {json.dumps({"text": text, "color": "gold"}, ensure_ascii=True)}'

    with socket.create_connection((host, port), timeout=10) as sock:
        sock.settimeout(10)
        _rcon_send(sock, 1, 3, CONFIG["rcon_password"])
        auth_id, _, _ = _rcon_read(sock)
        if auth_id == -1:
            raise RuntimeError("Fallo autenticacion RCON")
        _rcon_send(sock, 2, 2, command)
        _rcon_read(sock)


def parse_iso(value: str):
    if not value:
        return None
    try:
        fixed = value.replace("Z", "+00:00")
        return datetime.fromisoformat(fixed)
    except ValueError:
        return None


def should_repeat(last_sent_iso: str, repeat_hours: int) -> bool:
    if repeat_hours <= 0:
        return False
    last_sent = parse_iso(last_sent_iso)
    if last_sent is None:
        return True
    return datetime.now(timezone.utc) - last_sent >= timedelta(hours=repeat_hours)


def build_update_message(local, remote) -> str:
    current = local.get("version_id") or "desconocida"
    target = remote.get("version_number") or remote.get("id") or "desconocida"
    published = remote.get("date_published") or "fecha desconocida"
    return (
        f"[CobbleVerse] Update disponible: {current} -> {target} (publicado: {published}). "
        "Recomendado: ./scripts/update-safe.sh"
    )


def run_check_once() -> int:
    state = load_json(CONFIG["state_file"], {})
    local = read_local_manifest(CONFIG["manifest_path"])

    if not local.get("version_id"):
        log("No se encontro version local en /data/.modrinth-modpack-manifest.json")
        state["last_check_at"] = now_iso()
        state["last_status"] = "local-manifest-missing"
        save_json(CONFIG["state_file"], state)
        return 0

    try:
        remote = fetch_latest_release(
            local.get("project_slug", CONFIG["project_slug"]),
            CONFIG["loader"],
            CONFIG["game_version"],
        )
    except Exception as exc:
        log(f"No se pudo consultar Modrinth: {exc}")
        state["last_check_at"] = now_iso()
        state["last_status"] = "remote-query-failed"
        save_json(CONFIG["state_file"], state)
        return 0

    state["last_check_at"] = now_iso()
    state["local_version_id"] = local.get("version_id")
    state["remote_version_id"] = remote.get("id")
    state["remote_version_number"] = remote.get("version_number")

    if local.get("version_id") == remote.get("id"):
        state["last_status"] = "up-to-date"
        log(f"Sin cambios. Version actual: {remote.get('version_number')}")
        save_json(CONFIG["state_file"], state)
        return 0

    state["last_status"] = "update-available"
    update_message = build_update_message(local, remote)
    log(update_message)

    last_notified_version = state.get("last_notified_version_id")
    first_notification_for_this_version = last_notified_version != remote.get("id")

    if CONFIG["notify_discord"] and first_notification_for_this_version:
        try:
            post_discord(update_message)
            log("Notificacion enviada a Discord")
        except Exception as exc:
            log(f"Fallo notificacion Discord: {exc}")

    if CONFIG["notify_minecraft"]:
        can_send_minecraft = first_notification_for_this_version or should_repeat(
            state.get("last_notified_minecraft_at", ""), CONFIG["minecraft_repeat_hours"]
        )
        if can_send_minecraft:
            try:
                send_minecraft_message(update_message)
                state["last_notified_minecraft_at"] = now_iso()
                log("Notificacion enviada al chat de Minecraft")
            except Exception as exc:
                log(f"Fallo notificacion Minecraft: {exc}")

    if first_notification_for_this_version:
        state["last_notified_version_id"] = remote.get("id")
        state["last_notified_at"] = now_iso()

    save_json(CONFIG["state_file"], state)
    return 0


def run_loop() -> int:
    interval_hours = max(CONFIG["interval_hours"], 1)
    interval_seconds = interval_hours * 3600

    if not CONFIG["enabled"]:
        log("UPDATE_CHECK_ENABLED=false. Checker en espera")
        while True:
            time.sleep(interval_seconds)

    if CONFIG["check_on_start"]:
        run_check_once()

    while True:
        time.sleep(interval_seconds)
        run_check_once()


CONFIG = {
    "enabled": env_bool("UPDATE_CHECK_ENABLED", True),
    "check_on_start": env_bool("UPDATE_CHECK_ON_START", True),
    "interval_hours": env_int("UPDATE_CHECK_INTERVAL_HOURS", 168),
    "notify_log": env_bool("UPDATE_NOTIFY_LOG", True),
    "notify_discord": env_bool("UPDATE_NOTIFY_DISCORD", False),
    "discord_webhook": os.getenv("UPDATE_NOTIFY_DISCORD_WEBHOOK", ""),
    "notify_minecraft": env_bool("UPDATE_NOTIFY_MINECRAFT", False),
    "minecraft_repeat_hours": env_int("UPDATE_NOTIFY_MINECRAFT_REPEAT_HOURS", 24),
    "manifest_path": Path(os.getenv("LOCAL_MANIFEST_PATH", "/data/.modrinth-modpack-manifest.json")),
    "state_file": Path(os.getenv("UPDATE_CHECK_STATE_FILE", "/state/state.json")),
    "project_slug": os.getenv("MODRINTH_PROJECT_SLUG", "cobbleverse"),
    "loader": os.getenv("MODRINTH_LOADER", "fabric"),
    "game_version": os.getenv("MODRINTH_GAME_VERSION", "1.21.1"),
    "rcon_host": os.getenv("RCON_HOST", "mc-evolution"),
    "rcon_port": env_int("RCON_PORT", 25575),
    "rcon_password": os.getenv("RCON_PASSWORD", ""),
}


def main() -> int:
    mode = sys.argv[1] if len(sys.argv) > 1 else "loop"
    if mode == "check-once":
        return run_check_once()
    if mode == "loop":
        return run_loop()
    print("Uso: update-checker.py [check-once|loop]", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
