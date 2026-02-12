# Minecraft Docker CobbleVerse Rubius

Servidor de Minecraft inspirado en la serie de Rubius, listo para correr con Docker usando **CobbleVerse** en Fabric.

La idea de este repo es simple: clonar, levantar con un comando y jugar.

## Que incluye

- Modpack `cobbleverse` (Modrinth) en `1.21.1`.
- Instalacion automatica de mods extra (LuckPerms, Chunky y addons compatibles).
- Pregeneracion automatica de mapa al iniciar (Overworld/Nether/End).
- Backup automatico diario.
- Configuracion optimizada para host de 16 GB.
- Datapack extra compatible: `CCC_2.0.zip`.

## Inicio rapido

1. Clona el repo.
2. Crea tu `.env` desde el ejemplo:

```bash
cp .env.example .env
```

3. Abre `.env` y cambia `RCON_PASSWORD` por una clave fuerte (larga y unica).

Ejemplo:

```env
RCON_PASSWORD=pon-aqui-una-clave-larga-y-segura
```

`RCON_PASSWORD` debe ser igual para `mc-evolution` y `mc-backup`; por eso se define una sola vez en `.env`.

Tambien puedes ajustar zona horaria (por defecto Peru):

```env
SERVER_TZ=America/Lima
```

Si no existe `.env` o no tiene `RCON_PASSWORD`, Docker Compose fallara al arrancar para evitar un despliegue inseguro.

4. Levanta el servidor:

```bash
docker compose up -d
```

5. Mira logs:

```bash
docker logs -f mc-evolution-16gb
```

Listo. El servidor descarga lo necesario y arranca solo.

## Pregeneracion automatica

Al arrancar, Chunky inicia automaticamente:

- Overworld: radio 5000
- Nether: radio 2500
- End: radio 2000

Ademas:

- Primer jugador entra -> `chunky pause`
- Ultimo jugador sale -> `chunky continue`

## Archivos importantes

- `docker-compose.yml`: configuracion principal del servidor.
- `docker-compose.local.yml`: perfil de bajo consumo para pruebas locales (1G/2G).
- `docker-compose.arclight.yml`: plantilla futura para probar Arclight.
- `config/`: overrides de configuracion que se copian al servidor.
- `data/datapacks/`: datapacks incluidos en el repo.
- `scripts/update-safe.sh`: actualizacion segura con backup previo.
- `scripts/rollback-last-update.sh`: rollback rapido al ultimo backup.
- `.env.example`: variables de entorno recomendadas para secretos e imagenes.

## Actualizar sin miedo

```bash
./scripts/update-safe.sh
```

Si algo sale mal:

```bash
./scripts/rollback-last-update.sh
```

Opcional: pasar un backup especifico

```bash
./scripts/rollback-last-update.sh 20260212-142530
```

## Variables recomendadas

- `RCON_PASSWORD`: clave secreta de RCON compartida entre servidor y backup (obligatoria).
- `SERVER_TZ`: zona horaria del servidor (`America/Lima` por defecto).
- `MC_BACKUP_IMAGE`: imagen de `mc-backup`; viene pineada por defecto para mantener estabilidad.
- `PRE_UPDATE_RETENTION_DAYS`: dias que se conservan backups pre-update antes de purgar antiguos.

Tip rapido: si actualizas el repo y aparece una variable nueva en `.env.example`, copiala tambien a tu `.env`.

## Chequeo automatico de actualizaciones (opcional)

El servicio `update-checker` viene integrado en `docker-compose.yml` para revisar nuevas versiones de CobbleVerse sin tocar tu mundo.

Comportamiento por defecto:

- Revisa una vez al iniciar el stack.
- Luego vuelve a revisar cada semana (`168` horas).
- Solo **avisa**; no actualiza automaticamente.
- Puedes activar avisos en logs, Discord y chat de Minecraft de forma independiente.

### Logica del checker

1. Lee version local desde `data/.modrinth-modpack-manifest.json`.
2. Consulta Modrinth para la ultima release compatible (`cobbleverse`, `fabric`, `1.21.1`).
3. Compara `versionId` local vs remoto.
4. Si hay update:
   - muestra aviso en logs (si esta habilitado),
   - envia webhook a Discord (si esta habilitado),
   - envia mensaje in-game con `tellraw @a` por RCON (si esta habilitado).
5. Evita spam: guarda estado en `backups/update-check/state.json` y no repite la misma alerta cada ciclo.

### Variables del checker

- `UPDATE_CHECK_ENABLED=true`: activa/desactiva el checker.
- `UPDATE_CHECK_ON_START=true`: chequea al iniciar.
- `UPDATE_CHECK_INTERVAL_HOURS=168`: cada cuantas horas revisar (168 = semanal).
- `UPDATE_NOTIFY_LOG=true`: avisar en logs de Docker.
- `UPDATE_NOTIFY_DISCORD=false`: activar aviso por Discord.
- `UPDATE_NOTIFY_DISCORD_WEBHOOK=`: webhook de Discord (solo si activas Discord).
- `UPDATE_NOTIFY_MINECRAFT=false`: activar aviso dentro del juego.
- `UPDATE_NOTIFY_MINECRAFT_REPEAT_HOURS=24`: repetir aviso in-game si sigue pendiente.
- `MODRINTH_PROJECT_SLUG=cobbleverse`: slug del modpack.
- `MODRINTH_LOADER=fabric`: loader objetivo.
- `MODRINTH_GAME_VERSION=1.21.1`: version del juego objetivo.

### Escenarios comunes

Solo logs:

```env
UPDATE_NOTIFY_LOG=true
UPDATE_NOTIFY_DISCORD=false
UPDATE_NOTIFY_MINECRAFT=false
```

Logs + Discord:

```env
UPDATE_NOTIFY_LOG=true
UPDATE_NOTIFY_DISCORD=true
UPDATE_NOTIFY_DISCORD_WEBHOOK=https://discord.com/api/webhooks/...
UPDATE_NOTIFY_MINECRAFT=false
```

Logs + aviso dentro de Minecraft (para todos los jugadores):

```env
UPDATE_NOTIFY_LOG=true
UPDATE_NOTIFY_DISCORD=false
UPDATE_NOTIFY_MINECRAFT=true
UPDATE_NOTIFY_MINECRAFT_REPEAT_HOURS=24
```

Desactivar completamente el checker:

```env
UPDATE_CHECK_ENABLED=false
```

### Chequeo manual

Puedes lanzar una revision puntual sin esperar al ciclo semanal:

```bash
docker compose run --rm update-checker python /scripts/update-checker.py check-once
```

### Flujo recomendado cuando detecte update

1. Revisar changelog del modpack.
2. Ejecutar actualizacion segura:

```bash
./scripts/update-safe.sh
```

3. Validar logs del servidor:

```bash
docker logs -f mc-evolution-16gb
```

4. Si falla algo, rollback:

```bash
./scripts/rollback-last-update.sh
```

### Troubleshooting rapido

- No llega Discord: verifica `UPDATE_NOTIFY_DISCORD=true` y `UPDATE_NOTIFY_DISCORD_WEBHOOK`.
- No llega mensaje in-game: verifica `ENABLE_RCON=true`, `RCON_PASSWORD` y que el servidor este encendido.
- No detecta version local: espera a que el servidor genere `data/.modrinth-modpack-manifest.json` tras el primer arranque.
- Si no quieres ningun aviso externo, deja solo logs o apaga el checker.

## Notas

- Este proyecto es comunitario/fan-made para facilitar el setup.
- No es un servicio oficial de Mojang/Microsoft.
- Revisa licencias de addons/datapacks para uso publico/comercial.
