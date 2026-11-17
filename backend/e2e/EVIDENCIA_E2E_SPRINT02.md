# Evidencia E2E Sprint 02 · API v2 contra stack Docker real

- Fecha (UTC): 2026-11-17T23:45:31+00:00
- API: `http://localhost:18000` · Keycloak: `http://localhost:18080` realm `crm-rah-dev` cliente `crm-rah-app`
- Token real de usuario-a: iss `http://localhost:18080/realms/crm-rah-dev`, aud `crm-rah-api`, sub `e0000000-0000-4000-8000-000000000001` (sin imprimir el token)
- Resultado: **39/39 comprobaciones OK**

| Fila de la matriz | Comprobación | Resultado | Detalle |
| --- | --- | --- | --- |
| Identidad | token real Keycloak: iss/aud/sub | OK | iss=http://localhost:18080/realms/crm-rah-dev aud=['crm-rah-api'] sub=e0000000-0000-4000-8000-000000000001 |
| Identidad | GET /me usuario-a → solo Caracas | OK | status=200 |
| A y B crean misma referencia | E2E-234520 en ambas, IDs distintos | OK | 201/201 |
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
| Sin sesión | GET /api/v2/organizaciones/11111111-1111-4111-8111-111111111111/inmuebles/63101706-3c43-48c4-b689-c07e62795f6a/media → 401 | OK | 401 |
| Sin sesión | POST /api/v2/organizaciones/11111111-1111-4111-8111-111111111111/inmuebles/63101706-3c43-48c4-b689-c07e62795f6a/media → 401 | OK | 401 |
| Sin sesión | GET /api/v2/me → 401 | OK | 401 |
| Sin sesión | token con firma alterada → 401 | OK | 401 |
| Rol insuficiente | marketing intenta borrar miembro → 403 | OK | 403 |
| Rol insuficiente | asesor intenta borrar miembro → 403 | OK | 403 |
| Rol insuficiente | marketing intenta subir foto → 403 | OK | 403 |
| Rol insuficiente | asesor intenta editar → 403 | OK | 403 |
| Usuario dual | selección Caracas → solo Caracas | OK | 5 filas |
| Usuario dual | selección Valencia → solo Valencia | OK | 2 filas |
| Usuario dual | inmueble de Valencia bajo selección Caracas → 404 | OK | 404 |
| API v1 deshabilitada | GET /api/v1/inmuebles → 404 | OK | 404 |
| API v1 deshabilitada | GET /api/v1/inmuebles/63101706-3c43-48c4-b689-c07e62795f6a → 404 | OK | 404 |
| API v1 deshabilitada | GET /api/v1/inmuebles/63101706-3c43-48c4-b689-c07e62795f6a/media → 404 | OK | 404 |
| Revocación con sesión abierta | propietario revoca membresía Caracas de usuario-ab → 204 | OK | 200/204 |
| Revocación con sesión abierta | mismo token, siguiente request en Caracas → 403 | OK | 403 |
| Revocación con sesión abierta | membresía Valencia intacta → 200 | OK | 200 |
| RLS / pool | rah_app sin SUPERUSER ni BYPASSRLS | OK |  |
| RLS / pool | consulta sin contexto → 0 filas | OK | 0 filas |
| RLS / pool | consulta sin filtro con contexto Caracas → solo Caracas | OK | {'11111111-1111-4111-8111-111111111111'} |

## Limitaciones de esta corrida

- Tras la revocación, la membresía se reactiva directamente en BD para dejar el entorno DEV como estaba (no existe endpoint de reactivación).
- Datos 100 % ficticios.

## Condiciones de la corrida

- Stack levantado **desde cero** (proyecto Docker `crm-rah-verif`, volúmenes nuevos) con el `compose.yaml`
  real de la rama (incluye `sprint02-db` 76e6b37: MinIO de Chainguard fijado por digest). Único override:
  puertos (`backend/e2e/compose/reset-ports.yaml` + `e2e-ports.yaml`) por choque con otros servicios
  locales: Postgres `127.0.0.1:15432`, Keycloak `127.0.0.1:18080`, backend `127.0.0.1:18000`;
  `OIDC_ISSUER=http://localhost:18080/realms/crm-rah-dev`.
- `minio-init` creó el bucket tras reintentar mientras MinIO arrancaba.
- BD: `db/init.sql` (arranque del volumen) → **`alembic upgrade head`** (0001 → 0002, CLI real) →
  `db/seeds/0001_sprint02_seeds.sql` con `psql`. `alembic current` = `0002_rls_usuario_lectura (head)`.
- Usuarios reales del realm DEV: usuario-a, usuario-b, usuario-ab, usuario-propietario, usuario-marketing.
- Backend: imagen de `backend/Dockerfile` (Python 3.12), conectado como `rah_app`; `GET /health` 200.
- Frontend: no levantado.

Comando (desde la raíz, con `.env` basado en `.env.example` y el `OIDC_ISSUER` de arriba):

```bash
docker compose -f compose.yaml -f backend/e2e/compose/reset-ports.yaml \
  -f backend/e2e/compose/e2e-ports.yaml up -d --build postgres minio minio-init keycloak backend
(cd db && DATABASE_URL=postgresql://rah_dev:<dev>@localhost:15432/rah_vzla alembic upgrade head)
docker compose exec -T postgres psql -U rah_dev -d rah_vzla < db/seeds/0001_sprint02_seeds.sql
cd backend && E2E_API=http://localhost:18000 E2E_KEYCLOAK=http://localhost:18080 E2E_PASSWORD=<dev> \
  E2E_ADMIN_DB_URL=postgresql://rah_dev:<dev>@localhost:15432/rah_vzla \
  E2E_APP_DB_URL=postgresql://rah_app:<dev>@localhost:15432/rah_vzla \
  python e2e/run_e2e.py --salida e2e/EVIDENCIA_E2E_SPRINT02.md
```
