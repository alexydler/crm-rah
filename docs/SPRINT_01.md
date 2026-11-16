# Sprint 01 · CRM mínimo verificable

## Definición de terminado

- [ ] `docker compose up --build -d` inicia Postgres, MinIO, FastAPI y Next.js sin errores.
- [ ] `curl http://localhost:8000/health` devuelve `status=ok`.
- [ ] `GET /api/v1/inmuebles` devuelve las tres propiedades DEMO.
- [ ] Desde `http://localhost:3000` se crea y consulta un inmueble nuevo.
- [ ] En el detalle se sube una fotografía JPG/PNG/WEBP y se visualiza la previsualización mediante URL temporal.
- [ ] Se comprueba que la fotografía original no se altera ni lleva marca de agua.
- [ ] Se documentan CORS, errores y pruebas manuales en el README.

## No incluido en sprint 01

MCP operativo, reels, PDFs de contratos jurídicos, 3D, publicación a portales, IA en producción, autenticación, datos reales. Esta separación es deliberada.

## Prompt para Antigravity

> Actúa como DevOps y DBA. Trabaja solo en `compose.yaml`, `db/` e `infra/` del repositorio existente. Lee `CONTRACTS.md`. Verifica red/puertos de loopback, healthcheck de PostgreSQL, inicialización idempotente de MinIO, persistencia de volúmenes y datos de prueba. No recrees el frontend ni el backend. Informa de cualquier fallo reproducible con comandos y salida. No uses credenciales de producción.

## Prompt para Claude Code

> Actúa como backend engineer. Trabaja solo en `backend/` y `mcp-server/`. Lee `CONTRACTS.md`. Audita y prueba la API FastAPI y el almacenamiento privado de medios. Completa pruebas unitarias y de integración sin alterar contratos acordados. No implementes contratos jurídicos definitivos ni publicación real. Los endpoints futuros deben quedar explícitamente sin implementar. Devuelve lista de archivos, comandos ejecutados y riesgos.

## Prompt para OpenCode

> Actúa como frontend engineer. Trabaja solo en `frontend/`. Lee `CONTRACTS.md`. Mejora la interfaz del CRM, estados de error/carga, formularios y galería, consumiendo exactamente la API acordada. No crees endpoints ficticios ni edites `backend/templates/`. Diseña para escritorio y móvil. Mantén los datos DEMO identificados. Devuelve pruebas y capturas si el entorno permite verificarlas.
