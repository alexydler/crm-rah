# Evidencia E2E Sprint 02 · API v2 contra stack Docker real

- Fecha (UTC): 2026-11-17T23:33:56+00:00
- API: `http://localhost:18000` · Keycloak: `http://localhost:18080` realm `crm-rah-dev` cliente `crm-rah-app`
- Token real de usuario-a: iss `http://localhost:18080/realms/crm-rah-dev`, aud `crm-rah-api`, sub `e0000000-0000-4000-8000-000000000001` (sin imprimir el token)
- Resultado: **36/36 comprobaciones OK**

| Fila de la matriz | Comprobación | Resultado | Detalle |
| --- | --- | --- | --- |
| Identidad | token real Keycloak: iss/aud/sub | OK | iss=http://localhost:18080/realms/crm-rah-dev aud=['crm-rah-api'] sub=e0000000-0000-4000-8000-000000000001 |
| Identidad | GET /me usuario-a → solo Caracas | OK | status=200 |
| A y B crean misma referencia | E2E-233340 en ambas, IDs distintos | OK | 201/201 |
| A y B crean misma referencia | precio string decimal | OK |  |
| A y B crean misma referencia | duplicado en la misma org → 409 | OK | 409 |
| A consulta recursos de B | listado de Valencia → 403 | OK | 403 |
| A consulta recursos de B | UUID de B bajo su org → 404 | OK | 404 |
| A consulta recursos de B | UUID de B bajo org B → 403 | OK | 403 |
| A consulta recursos de B | listado propio sin filas de B | OK | 4 filas |
| A manipula organizacion_id | JSON con organizacion_id → 422 | OK | 422 |
| A manipula organizacion_id | cabecera X-Organization-ID ignorada (queda en Caracas) | OK | 201 |
| A manipula organizacion_id | URL con org B → 403 | OK | 403 |
| A manipula organizacion_id | ningún registro creado en Valencia | OK | 0 filas |
| Fotos privadas | gerente (usuario-ab) sube foto a Caracas → 201 | OK | 201 |
| Fotos privadas | clave con prefijo organizaciones/{org}/inmuebles/{id}/ | OK |  |
| Fotos privadas | URL firmada abre desde el host (MinIO real) | OK | status=200 |
| Fotos privadas | mismo objeto sin firma → denegado por MinIO | OK | status=403 |
| B pide URL temporal de A | org A en URL → 403 sin URL | OK | 403 |
| B pide URL temporal de A | org B en URL → 404 sin URL | OK | 404 |
| Sin sesión | GET /api/v2/organizaciones/11111111-1111-4111-8111-111111111111/inmuebles/cb322a67-3d15-4a53-8d86-e8a5d330cba0/media → 401 | OK | 401 |
| Sin sesión | POST /api/v2/organizaciones/11111111-1111-4111-8111-111111111111/inmuebles/cb322a67-3d15-4a53-8d86-e8a5d330cba0/media → 401 | OK | 401 |
| Sin sesión | GET /api/v2/me → 401 | OK | 401 |
| Sin sesión | token con firma alterada → 401 | OK | 401 |
| Rol insuficiente | asesor intenta borrar la membresía de otro → 403 | OK | 403 |
| Rol insuficiente | asesor intenta editar → 403 | OK | 403 |
| Usuario dual | selección Caracas → solo Caracas | OK | 5 filas |
| Usuario dual | selección Valencia → solo Valencia | OK | 2 filas |
| Usuario dual | inmueble de Valencia bajo selección Caracas → 404 | OK | 404 |
| API v1 deshabilitada | GET /api/v1/inmuebles → 404 | OK | 404 |
| API v1 deshabilitada | GET /api/v1/inmuebles/cb322a67-3d15-4a53-8d86-e8a5d330cba0 → 404 | OK | 404 |
| API v1 deshabilitada | GET /api/v1/inmuebles/cb322a67-3d15-4a53-8d86-e8a5d330cba0/media → 404 | OK | 404 |
| Revocación con sesión abierta | mismo token, membresía Caracas inactiva → 403 | OK | 403 |
| Revocación con sesión abierta | membresía Valencia intacta → 200 | OK | 200 |
| RLS / pool | rah_app sin SUPERUSER ni BYPASSRLS | OK |  |
| RLS / pool | consulta sin contexto → 0 filas | OK | 0 filas |
| RLS / pool | consulta sin filtro con contexto Caracas → solo Caracas | OK | {'11111111-1111-4111-8111-111111111111'} |

## Limitaciones de esta corrida

- El realm DEV no tiene usuarios `marketing` ni `propietario`: el 403 por rol se probó con `asesor`; el caso exacto `marketing` y el DELETE de membresías por propietario están cubiertos por los tests de integración (`tests/test_v2_aislamiento.py`).
- La revocación se simuló marcando la membresía `inactiva` en BD (y se restauró), con el token ya emitido.
- Datos 100 % ficticios.

## Condiciones de la corrida

- Stack: `compose.yaml` de la rama `sprint02-backend` (incluye `sprint02-db` c8f7581) + overrides en
  `backend/e2e/compose/`, SIN modificar `compose.yaml`:
  - `reset-ports.yaml` + `e2e-ports.yaml`: Postgres en `127.0.0.1:15432`, Keycloak en `127.0.0.1:18080`
    y backend en `127.0.0.1:18000`, por choque con otros servicios locales (5432, 8000, 8080).
    `OIDC_ISSUER=http://localhost:18080/realms/crm-rah-dev`.
  - `minio-chainguard.yaml`: las imágenes `minio/minio` y `minio/mc` (Docker Hub y quay.io) responden
    "access denied"; se usó `cgr.dev/chainguard/minio` (MinIO RELEASE.2026-11-16T00-11-40Z) y
    `cgr.dev/chainguard/minio-client`. **Pendiente infra:** fijar una imagen disponible en `compose.yaml`.
- BD: volumen nuevo; `db/init.sql` (arranque) + `0001` + `0002` + `db/seeds/0001_sprint02_seeds.sql`
  aplicados con `psql` (vía SQL documentada en `infra/README.md`); `alembic_version` = `0002_rls_usuario_lectura`.
  No se ejecutó el CLI de Alembic.
- Backend: imagen construida desde `backend/Dockerfile` (Python 3.12.16), conectado como `rah_app`; `GET /health` 200.
- Frontend: no levantado (fuera del alcance de esta prueba).

Comando (desde la raíz del repo, con `.env` basado en `.env.example` + `OIDC_ISSUER` de arriba):

```bash
docker compose -f compose.yaml -f backend/e2e/compose/reset-ports.yaml \
  -f backend/e2e/compose/e2e-ports.yaml -f backend/e2e/compose/minio-chainguard.yaml \
  up -d --build postgres minio minio-init keycloak backend
# migraciones/seeds con psql; luego, desde backend/:
E2E_API=http://localhost:18000 E2E_KEYCLOAK=http://localhost:18080 E2E_PASSWORD=<dev> \
E2E_ADMIN_DB_URL=postgresql://rah_dev:<dev>@localhost:15432/rah_vzla \
E2E_APP_DB_URL=postgresql://rah_app:<dev>@localhost:15432/rah_vzla \
python e2e/run_e2e.py --salida e2e/EVIDENCIA_E2E_SPRINT02.md
```
