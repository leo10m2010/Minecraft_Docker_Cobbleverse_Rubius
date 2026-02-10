# Docker Agent Profile - Evolution Server

Este archivo define el perfil operativo para desplegar el servidor en host objetivo de 16 GB RAM.

## Objetivo

- Base del servidor: Modpack `COBBLEVERSE` (Modrinth) en `1.21.1`.
- Runtime estable: Fabric via `TYPE=MODRINTH`.
- Extras: LuckPerms, Chunky y lista adicional integrada en `MODRINTH_PROJECTS`.
- Migracion futura: Arclight mediante override dedicado (`docker-compose.arclight.yml`).
- Prioridad: estabilidad en host de 16 GB antes que maximo rendimiento bruto.

## Reglas operativas

1. No ejecutar el stack en esta maquina local de 16 GB durante preparacion.
2. Mantener Java 21 para Minecraft 1.21.1.
3. Usar instalacion automatica por Modrinth para mantener dependencias sincronizadas.
4. Mantener addons en `MODRINTH_PROJECTS` priorizando variantes Fabric.
4.1. Para actualizaciones continuas, no fijar `MODRINTH_VERSION` ni versiones de proyecto salvo contingencia.
5. No mezclar versiones viejas de mods 1.20.1 en entorno 1.21.1.
6. Solo habilitar Arclight cuando su Fabric Loader sea compatible con el modpack objetivo.

## Parametros recomendados para 16 GB

- `INIT_MEMORY=6G`
- `MAX_MEMORY=12G`
- `USE_MEOWICE_FLAGS=true`
- `VIEW_DISTANCE=8`
- `SIMULATION_DISTANCE=6`
- `SYNC_CHUNK_WRITES=false`

## Seguridad minima

- Cambiar `RCON_PASSWORD` antes de subir.
- No exponer RCON a internet.
- Mantener backups diarios con retencion.

## Validacion post-despliegue

1. Verificar que Modrinth instale `cobbleverse` sin errores.
2. Verificar que no existan jars heredados incompatibles (ej. Cardboard 1.20).
3. Verificar carga de LuckPerms Fabric y Chunky Fabric.
4. Validar TPS y GC con spark bajo carga real.
