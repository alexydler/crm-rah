# CRM RAH VZLA · Contratos ejecutables v0.2 + propuesta v0.3

**Estado claro:** lo definido abajo en v0.2 es el contrato del prototipo local monoempresa; la nueva arquitectura y API v2 para todas las inmobiliarias venezolanas se definen en `docs/ARQUITECTURA_MULTIAGENCIA.md` y `docs/CONTRATO_API_V2_PROPUESTO.md` como propuestas para implementar en Sprint 02. No declarar que existe autenticación o multitenancy. Antes de cambiar este archivo, revisar impacto con los tres agentes.

## Mapa de responsabilidades

- **Antigravity:** `compose.yaml`, `db/`, `infra/`; no modifica frontend ni backend.
- **Claude Code:** `backend/`, `mcp-server/`; consume los modelos/contratos acordados.
- **OpenCode:** `frontend/` y `design/` (opcional); NO modifica `backend/templates/`.
- **Plantillas de render:** OpenCode entrega HTML/CSS en `frontend/design-templates/` (futuro); Claude valida y copia/publica en `backend/templates/`. El propietario final de `backend/templates/` es Claude.
- **Archivos compartidos:** `CONTRACTS.md`, `docs/` y la raíz se modifican solo tras revisión del integrador humano.

## Datos principales

### Inmueble

```json
{
  "id": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1",
  "titulo": "DEMO · Apartamento ficticio",
  "tipo": "apartamento",
  "operacion": "venta",
  "precio": "85000.00",
  "moneda": "USD",
  "direccion": null,
  "zona": "Caracas · ubicación ficticia",
  "estado_ve": "Miranda",
  "municipio": "Baruta",
  "parroquia": null,
  "urbanizacion": "Zona ficticia",
  "codigo_referencia": "DEMO-RAH-001",
  "m2_construidos": "88.00",
  "m2_parcela": null,
  "habitaciones": 3,
  "banos": 2,
  "extras": {"terraza": true},
  "descripcion": "Registro de prueba",
  "estado": "borrador"
}
```

Enumeraciones: `tipo=apartamento|casa|quinta|townhouse|local|oficina|galpon|terreno`, `operacion=venta|alquiler`, `estado=borrador|disponible|reservado|cerrado`. Las superficies y habitaciones son opcionales según el tipo; nunca mostrar atributos vacíos en las piezas comerciales. Identificadores: UUID. Precio: decimal serializado como **string** en JSON para evitar errores de coma flotante. Moneda: **solo USD o VES** en esta fase; no hacer conversión ni inventar tasa de cambio. Los valores pertenecen a la moneda declarada.

### MediaAsset

```json
{
  "id": "uuid",
  "inmueble_id": "uuid",
  "tipo": "foto",
  "etiqueta_estancia": "salon",
  "orden": 0,
  "content_type": "image/jpeg",
  "url_temporal": "https://..."
}
```

Guardar `object_key` privado en base de datos, **jamás URLs firmadas**: se emiten con expiración al solicitar medios. Los originales no llevan marcas de agua. Las creatividades son derivados separados.

## API base

- `GET /health` → `200 {"status":"ok"}` si base de datos operativa.
- `GET /api/v1/inmuebles` → `200 Inmueble[]`; filtrable por `tipo` y `estado`.
- `POST /api/v1/inmuebles` → `201 Inmueble`; cuerpo `InmuebleCreate` sin `id`.
- `GET /api/v1/inmuebles/{uuid}` → `200 Inmueble` o `404`.
- `GET /api/v1/inmuebles/{uuid}/media` → `200 MediaAsset[]`.
- `POST /api/v1/inmuebles/{uuid}/media` (multipart, `archivo`, `etiqueta_estancia` opcional) → `201 MediaAsset`. Únicamente JPG/PNG/WEBP de hasta 12 MiB para esta fase.
- `GET /docs` → Swagger, **solo desarrollo local**.

Código HTTP de validación: `422`. El modelo de error sigue FastAPI: `{"detail": ...}`. Cualquier cambio de esquema obliga actualizar pruebas de contrato.

## Contratos futuros (NO IMPLEMENTADOS)

- `POST /api/v1/render/carrusel`: `{inmueble_id, plantilla, media_ids, branding}` → trabajo asíncrono y URL temporal; **sin publicación automática**.
- `POST /api/v1/render/reel`: `{inmueble_id, escenas, subtitulos, audio_asset_id?}` → trabajo asíncrono.
- `POST /api/v1/contratos/documento/borrador`: NO aplicable como plantilla española de arras: queda pendiente sustituir por borradores locales con revisión jurídica venezolana.
- `POST /api/v1/publicaciones/{canal}/exportar`: prevalidación y exportación; publicar en un portal solo tras acceso oficial y autorización.

## Fronteras de seguridad

- v0.2 **NO** tiene autenticación, roles, multiinquilino, auditoría de cambios, backups automáticos ni cumplimiento de protección de datos aplicable en Venezuela: **SOLO DATOS FICTICIOS Y HOST LOCAL**.
- Antes de ingresar datos reales de clientes: usuarios y roles, control de acceso, cifrado/secretos, política de retención, auditoría, backups, permisos de imagen y cumplimiento legal aplicable en Venezuela.
- Ningún agente firma contratos, publica anuncios, gasta presupuesto publicitario ni cambia estados críticos sin confirmación humana.

## Localización Venezuela — alcance

- Código interno de propiedad opcional, no sustituye el identificador oficial de una franquicia.
- Geografía: `zona` sigue siendo obligatoria por compatibilidad; `estado_ve`, `municipio`, `parroquia`, `urbanizacion` son opcionales.
- Precios: `USD` o `VES` por inmueble; no hay cambio automático ni tasa implícita.
- Publicidad: solamente exportación manual (Instagram, WhatsApp, Facebook, portales con acceso concedido); nunca importar o publicar en sistemas privados por scraping.
- CRM compartido multiagencia requiere consentimiento, permisos por organización, registro de acciones y políticas de acceso que aún NO existen.
- RAH se usa como nombre interno provisional; no implica licencia de marca, patrocinio o integración con Rent-A-House.

## Decisión aprobada para v0.3 (pendiente de implementar)

1. Producto multiempresa: cada inmobiliaria será `organizacion` con `organizacion_id` en todo recurso privado.
2. API nueva `/api/v2/organizaciones/{organizacion_id}/...`, identidad OIDC y membresía validada, permisos por rol.
3. PostgreSQL RLS + FK compuestas, prefijos privados S3 y URLs temporales tras autorización; no fiarse de org id enviado por cliente.
4. Marca/branding por empresa; misma plataforma, clientes/carteras aislados.
5. Migrar con Alembic: nunca dar por hecho que `db/init.sql` actualizará volúmenes existentes.
6. Pruebas de aislamiento A/B bloqueantes antes de usar datos reales o comenzar factory de marketing.
7. Ver `docs/SPRINT_02_MULTIAGENCIA.md`; el contenido de las secciones v0.2 anterior no cambia hasta que termine la migración.
