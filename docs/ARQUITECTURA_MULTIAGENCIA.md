# ADR-001 · CRM RAH VZLA multiinmobiliaria (v0.3, diseño aprobado)

**Decisión:** la plataforma sirve a cualquier inmobiliaria venezolana, no solo a una franquicia.
**Estado del código:** arquitectura aprobada / implementación pendiente. La v0.2 local sigue siendo MONOEMPRESA y NO permite datos reales. Este documento NO activa aislamiento multiempresa ni sustituye migraciones.

## Propuesta de valor

SaaS B2B que une un CRM de captación/venta con una fábrica de marketing (fichas, historias, carruseles, reels y materiales con marca propia). El diferencial a validar con usuarios es la velocidad y calidad de producción comercial, no el simple catálogo de inmuebles.

## Unidad de aislamiento

- `organizacion` = una inmobiliaria independiente (tenant). Posee sus datos y marca. `organizacion_id UUID NOT NULL` debe existir en cada recurso privado: inmuebles, imágenes, clientes, oportunidades, conversaciones, visitas, publicaciones, diseños, tareas, contratos, trabajos de render y auditoría.
- `sucursal` = oficina de una organización, no un tenant. En la primera versión, sucursales son opcionales. Un usuario puede pertenecer a varias organizaciones mediante membresías distintas.
- No se comparte la libreta de contactos ni los propietarios entre agencias. La colaboración futura se hará mediante una entidad de autorización explícita a inmuebles compartidos, jamás quitando filtros de tenant.
- La referencia de inmueble es **única por organización**, no global: `UNIQUE(organizacion_id, codigo_referencia)` cuando `codigo_referencia IS NOT NULL`.
- `RAH` es un nombre provisional interno; no representa relación, afiliación, autorización o integración con Rent-A-House. Antes de comercializar, verificar disponibilidad legal de marca y cambiar nombre si corresponde.

## Arquitectura

```text
Navegador
   │ HTTPS
   ▼
Next.js (BFF + sesión de usuario, UI por organización)
   │ token servidor/servidor validado
   ▼
FastAPI (identidad verificada + membresía + rol + organización)
   ├── PostgreSQL 16: tablas con organizacion_id, FK compuestas, migraciones Alembic
   │   └── Row Level Security (RLS) como defensa adicional
   ├── MinIO/S3 privado: objetos por organizaciones/<uuid>/..., URLs firmadas tras autorización
   └── Workers de medios (posterior): trabajos con organizacion_id y límites por organización

Proveedor de identidad OIDC compatible (Keycloak local como opción de desarrollo; producto evaluará hospedaje).
MCP y agentes IA = servicio de ingeniería en esta fase; NUNCA permiten acceso transversal a inmobiliarias.
```

**Identificación:** OIDC Authorization Code + PKCE, sesiones de navegador seguras y verificación de tokens por el backend (`issuer`, `audience`, expiración, JWKS). El backend comprueba membresía activa *en base de datos* en cada operación. No crear contraseñas caseras ni autenticación fingida basada en cabeceras.

**Selección:** API v2 bajo `/api/v2/organizaciones/{organizacion_id}/...`. El ID en la URL solo identifica el recurso; NO autoriza. El servidor verifica membresía y permiso. Para recursos fuera de tenant, responder 404 para no revelar existencia. Deshabilitar API v1 sin autenticación antes de cualquier despliegue.

**Capas de aislamiento:**
1. Usuario autenticado y membresía activa (organización/rol) para cada solicitud.
2. Repositorios que obligan a pasar `organizacion_id`; operaciones por IDs se filtran simultáneamente por (organización, recurso).
3. PostgreSQL RLS para tablas tenant-scoped. Transacción usa `SET LOCAL` del tenant verificado; conexión normal no puede ser dueño de tablas, superusuario ni rol `BYPASSRLS`. Verificar `FORCE ROW LEVEL SECURITY` según necesidad y pool de conexiones.
4. Foreign keys compuestas `(organizacion_id, inmueble_id)` para impedir enlazar contactos, fotos u otros recursos de organizaciones distintas.
5. MinIO privado: keys `organizaciones/<uuid>/inmuebles/<uuid>/...`; el prefijo NO sustituye control de acceso. Comprobar autorización antes de emitir una URL firmada. No filtrar credenciales ni rutas privadas.

**Roles de organización (primera iteración):**
- `propietario`: configura su empresa, membresías y permisos.
- `gerente`: gestiona cartera, supervisa actividad de su agencia (no otros tenants).
- `asesor`: administra únicamente inmuebles/contactos asignados o explícitamente compartidos dentro de su empresa. Implementación por asignación será incremental; bloquear acciones no soportadas por permiso.
- `marketing`: lee fichas aprobadas y genera material; sin exportar datos privados de compradores.
- `consulta`: lectura de los inmuebles que su agencia le permita.
- `admin_plataforma`: rol separado, sin acceso automático al contenido privado; soporte extraordinario requiere autorización, justificación y registro auditable. No usar cuenta global como si fuera una agencia.

## Datos recomendados

| Tabla | Campos esenciales / decisión |
| --- | --- |
| `organizaciones` | id, slug, nombre_comercial, estatus, moneda_preferida, creado_en |
| `usuarios` | id, proveedor_auth, subject, email_normalizado, estado |
| `membresias` | organizacion_id, usuario_id, rol, estatus; `UNIQUE(organizacion_id, usuario_id)` |
| `sucursales` | organizacion_id, nombre, ubicación; opcional en v1 |
| `inmuebles` | organizacion_id obligatorio, referencia única por organización, asesor asignado (membresía de esa org), precio/moneda, ubicación Venezuela |
| `inmueble_media` | organizacion_id + inmueble_id (FK compuesta), object_key privada |
| `clientes` | organizacion_id + responsable, mínimo de datos, consentimiento/uso documentado |
| `oportunidades` | organizacion_id, inmueble_id, contacto_id, fase, responsable; posteriores al aislamiento |
| `marca_organizacion` | logo privado, colores, tipografía permitida, plantilla elegida |
| `auditoria_eventos` | organizacion_id, actor, acción, objetivo, fecha, correlación; sin datos personales sensibles en claro |

**No añadir aún** ML de valorización, facturación compleja, 3D, portales, marketplace entre agencias, contratos jurídicos automáticos ni publicación real.

## Políticas de propiedad y colaboración

- Registro `origen_captacion`: `propia`, `referida` o `compartida_autorizada`; usar solo tras validar qué datos pueden publicarse.
- Una agencia puede mostrar una ficha pública aprobada sin exponer el CRM interno. Si se habilita compartición entre agencias, diseñar `acuerdos_comparticion` con propietario de datos, receptor, alcance, expiración y revocación; no copiar teléfonos de propietarios por defecto.
- Nunca asumir conexiones autorizadas a portales o MLS privados de Venezuela. Los exportadores se crearán solo tras confirmar requisitos de cada canal.

## Branding y monetización

Una marca propia por agencia, aplicable a PDFs, imágenes y videos derivados. En el futuro: límites por plan en cantidad de asesores, propiedades, renders y almacenamiento (contar consumo por organización). **No fijar precios de SaaS sin validar disposición de pago con agencias.**

## Riesgos que bloquean datos reales

Falta autenticación y autorización de los endpoints actuales; falta migración y RLS; falta separación de medios, auditoría, backups/restore y retención de datos. El prototipo no debe exponerse públicamente. Revisar la normativa aplicable y los acuerdos de tratamiento de datos con asesoría jurídica en Venezuela.

## Fuentes técnicas utilizadas

- OWASP Multi Tenant Security Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Multi_Tenant_Security_Cheat_Sheet.html
- PostgreSQL 16 Row Security: https://www.postgresql.org/docs/16/ddl-rowsecurity.html
