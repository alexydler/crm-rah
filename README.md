# CRM RAH VZLA — Starter v0.3 (plan multiagencia; demo ejecutable v0.2)

Base **de desarrollo local** de un CRM inmobiliario (runtime v0.2; arquitectura v0.3 diseñada): Next.js, FastAPI, PostgreSQL 16 y MinIO. Incluye tres inmuebles 100% ficticios, altas de inmuebles, ficha detallada y carga de imágenes originales. NO incluye IA ejecutándose, MCP operativo, editor 3D, publicación, ni emisión de contratos; esos son hitos posteriores.


## Decisión v0.3: producto para todas las inmobiliarias venezolanas

- Modelo de negocio y arquitectura: **SaaS multitenant** para agencias inmobiliarias independientes, no exclusivo de una franquicia.
- **IMPORTANTE:** v0.3 incorpora diseño, contrato API propuesto y Sprint 02 para añadir el aislamiento. **El código ejecutable sigue siendo el prototipo monoempresa de v0.2.** Ni autenticación ni aislamiento están implementados. No admitir datos reales, no exponer por Internet, no ofrecer a clientes aún.
- Lectura obligatoria: `docs/ARQUITECTURA_MULTIAGENCIA.md`, `docs/CONTRATO_API_V2_PROPUESTO.md`, `docs/SPRINT_02_MULTIAGENCIA.md`, `db/design/ESQUEMA_OBJETIVO.md`.
- Prioridad del siguiente sprint: autenticación, organizaciones, roles, aislamiento de PostgreSQL/MinIO y pruebas cruzadas A/B. *Después*, fábrica de marketing por marca.
- Nombre `RAH` interno provisional, sin vínculo oficial ni licencia de Rent-A-House; revisar marca antes de comercializar.

## Requisitos

- Docker Desktop con Docker Compose v2; recursos sugeridos: 6 GB RAM libres.
- Puertos **3000, 8000, 9000, 9001 y 5432** libres en tu ordenador.
- Si el equipo no tiene Docker, usarlo primero en un ordenador con Docker; el sistema no está desplegado en nube.

## Arranque

```bash
cp .env.example .env
# revisa .env: son credenciales SOLO para desarrollo local
docker compose up --build -d
# tras arrancar
docker compose ps
curl http://localhost:8000/health
```

- **CRM:** http://localhost:3000
- **API:** http://localhost:8000/docs
- **MinIO local:** http://localhost:9001 (credenciales en `.env`)

Los puertos se vinculan a `127.0.0.1`; no se exponen en la red local por defecto. Las tres propiedades DEMO solo se insertan al crearse una base de datos nueva. Para leer logs: `docker compose logs -f backend` o `docker compose logs -f frontend`.

## Flujo de prueba

1. Abre el CRM y verifica tres elementos marcados `DEMO`.
2. Haz clic en **Nuevo inmueble**, completa los datos y guarda.
3. Abre la ficha del inmueble y sube una foto JPEG, PNG o WebP inferior a 12 MiB.
4. Comprueba que aparece la miniatura sin deformar y que el archivo está almacenado en el bucket privado `rah-vzla-media`.
5. Comprueba que `curl http://localhost:8000/api/v1/inmuebles` devuelve JSON.

## Comandos

```bash
docker compose down         # conserva datos
docker compose logs --tail=80 backend
docker compose down -v      # ELIMINA datos locales: solo para reiniciar DEMO
```

## Trabajo con tres agentes

Leer `CONTRACTS.md`, `AGENTS.md` y `docs/SPRINT_01.md` antes de dar prompts. Separar trabajo en ramas/worktrees y fusionar con tests. Nunca compartir credenciales reales en los prompts.

## Limitaciones verificadas

Este paquete se ha revisado **estáticamente** en el entorno de creación; no se ha arrancado Docker aquí porque el ejecutable Docker no estaba disponible. El primer paso en tu ordenador será ejecutar el checklist y corregir cualquier incompatibilidad del entorno antes de agregar funciones. Las versiones de contenedores son de desarrollo; auditarlas antes del despliegue.

## Ajustes de la versión Venezuela

- Nombre interno: **CRM RAH VZLA** (provisional, sin vínculo oficial presumido con Rent-A-House).
- Formulario con monedas USD/VES y estado/municipio/parroquia/urbanización.
- Nuevas categorías de inmueble y referencia interna opcional.
- Ejemplos ficticios de Caracas, Valencia y Maracaibo.
- Para no mezclar la versión anterior, esta copia utiliza un proyecto Compose, BD, usuario, bucket y volúmenes aislados.
- **Si tienes datos previos, no ejecutes `docker compose down -v` para migrarlos**. Los `init.sql` solo se aplican a un volumen nuevo. Para producción habrá que usar migraciones Alembic.

## Sobre ECC

ECC de `affaan-m/ECC` es una herramienta para **desarrollar** con Claude Code y otros agentes. NO está integrado como dependencia de ejecución del CRM. Ver `docs/ECC_ADOPCION.md`.
