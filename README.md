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
2. Crea tu `.env` desde el ejemplo y define `RCON_PASSWORD`.

```bash
cp .env.example .env
```

3. Levanta el servidor:

```bash
docker compose up -d
```

4. Mira logs:

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

- `RCON_PASSWORD`: secreto compartido entre servidor y backup.
- `MC_BACKUP_IMAGE`: imagen de `mc-backup` (viene pineada por defecto en `.env.example`).
- `PRE_UPDATE_RETENTION_DAYS`: dias a conservar en `backups/pre-update` antes de purgar.

## Notas

- Este proyecto es comunitario/fan-made para facilitar el setup.
- No es un servicio oficial de Mojang/Microsoft.
- Revisa licencias de addons/datapacks para uso publico/comercial.
