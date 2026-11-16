# Sprint 02 · De prototipo monoempresa a CRM multiinmobiliaria

## Objetivo del sprint

Implementar la **primera vertical multiempresa segura**: iniciar sesión, seleccionar inmobiliaria, crear/listar/ver inmuebles y gestionar fotografías *con aislamiento real*. Es prioritario sobre reels, 3D, MCP en producción o exportación a portales.

**Estado inicial:** en v0.2 `GET /api/v1/inmuebles` es público en localhost y no hay roles ni separación. No introducir datos reales ni publicar fuera de localhost hasta terminar estas tareas y comprobarlas.

## Secuencia obligatoria (en este orden lógico)

1. **Contrato y esquema:** acordar `docs/CONTRATO_API_V2_PROPUESTO.md`, entidades y permisos; convertir el SQL de referencia en migraciones Alembic reales, transaccionales y revisadas. No modificar `db/init.sql` asumiendo que reconfigurará bases existentes.
2. **Identidad:** conectar OIDC de desarrollo (p. ej., Keycloak local) con verificación de tokens real y sesiones seguras; crear usuarios A, B y usuario con dos membresías. Desactivar acceso anónimo a rutas v2.
3. **Aislamiento de BD:** asignar `organizacion_id NOT NULL` a todas las tablas de datos privados, índices `org_id + id` y clave de referencia por organización. Comprobar Foreign Keys compuestas, roles de BD sin `BYPASSRLS`, RLS y contexto verificado por transacción.
4. **API v2:** endpoints de `me`, organizaciones, inmuebles y fotos; validación de permisos por rol y pertenencia a organización. Nunca aceptar org del request como prueba de acceso.
5. **Almacenamiento privado:** prefijos de MinIO por organización y propiedad. URLs temporales tras revisar pertenencia. Probar que un enlace no puede ser emitido por usuario de otro tenant.
6. **Interfaz:** login real, selector de organización para quienes tengan varias, branding inicial por inmobiliaria, listado/formulario de inmuebles y estados de 401/403/404.
7. **Auditoría y pruebas:** log de creación/edición/descarga de medios (sin secretos), pruebas de integración de aislamiento y walkthrough en Docker.

## Matriz de pruebas de aceptación (bloqueantes)

| Prueba | Resultado requerido |
| --- | --- |
| A crea inmueble `REF-001`; B crea también `REF-001` | Ambos válidos, IDs diferentes |
| A consulta listado de B o su inmueble por UUID | 404 o acceso negado sin filtrar ficha |
| A cambia `organizacion_id` en JSON, URL o cabeceras | No logra acceder ni crear registros en B |
| B solicita URL temporal de imagen de A | Rechazado; no se emite URL |
| Usuario sin sesión intenta leer/cargar fotos | 401 |
| Usuario con rol `marketing` intenta borrar miembros | 403 |
| Usuario pertenece a A y B, cambia selección | Ve únicamente recursos de la organización seleccionada |
| API v1 se intenta consultar desde una URL pública | Deshabilitada; ninguna fuga de recursos DEMO |
| Revocación de membresía mientras sesión está abierta | Solicitudes posteriores rechazadas según política definida y probada |
| RLS / pool reutilizado después de atender A y luego B | No hay filas cruzadas, tampoco con consultas sin filtro deliberadas en tests |

## Distribución para tres agentes

### Antigravity — `db/`, `infra/`, `compose.yaml`

- Proponer y aplicar migraciones Alembic coordinadas con Claude; no reescribir datos sin copia.
- Añadir IdP local compatible OIDC con cuentas de prueba, sin credenciales predeterminadas para despliegue.
- Preparar dos organizaciones DEMO (Caracas y Valencia) y tres usuarios: solo A, solo B, ambos.
- Implementar configuración RLS y usuario de servicio no privilegiado. Pruebas de reset de contexto por transacción y restauración de backup de prueba.
- Documentar arranque y recuperación de volúmenes. Nunca ejecutar `docker compose down -v` si hay datos que conservar.

**Prompt para pegar:**

```text
Eres DBA/DevOps. Proyecto CRM RAH VZLA, SaaS multiinmobiliaria Venezuela. Lee CONTRACTS.md, docs/ARQUITECTURA_MULTIAGENCIA.md, docs/CONTRATO_API_V2_PROPUESTO.md y docs/SPRINT_02_MULTIAGENCIA.md. Trabaja SOLO en db/, infra/, compose.yaml y configuración de identidad previamente acordada. Prepara migración Alembic real (coordina con Claude propietario de backend), dos organizaciones de prueba, rol SQL sin BYPASSRLS y Row Level Security segura por transacción; valida unicidad de referencia por organización y ninguna FK cruzada. No edites el init.sql antiguo como sustituto de migración; conserva datos existentes. Incluye test reproducible de aislamiento, comandos exactos y evidencia. No habilites acceso de red pública.
```

### Claude Code (+ ECC controlado) — `backend/`, `mcp-server/`

- Implementar validación OIDC/JWKS de backend y dependencia `current_user` + membresía + rol activo.
- Crear endpoints API v2, repositorios tenant-aware y transacciones con contexto RLS.
- Proteger endpoints de medios, IDs y URL firmadas. Revisar inputs, timestamps y registros de auditoría.
- Hacer pruebas de integración PostgreSQL REAL, no solo mocks. Mantener v1 como DEMO local o deshabilitarla.
- MCP permanece desactivado para operaciones multiagencia hasta que implemente exactamente los mismos permisos y auditoría.

**Prompt para pegar:**

```text
Eres responsable Backend y Security. CRM RAH VZLA está pasando de monoempresa local a SaaS multiinmobiliaria. Lee CONTRACTS.md y los tres docs multiagencia. Trabaja SOLO backend/ y mcp-server/. Implementa verificación de tokens OIDC con iss/aud/JWKS, membresías verificadas en servidor, roles y autorización por recurso; API /api/v2/organizaciones/{org_id}/inmuebles y medios; queries con org verificada y RLS por transacción. Tests reales con organizaciones A/B y usuario dual: sin sesión 401, acceso cruzado 404, cambios org falsos sin efecto, fotos privadas, referencia repetida válida entre empresas. Coordina migración con DBA sin editar sus carpetas. No anuncies seguridad lista sin ejecutar las pruebas integrales.
```

### OpenCode — `frontend/` (y `frontend/design-templates` opcional)

- Crear flujo de acceso y estado de sesión con IdP acordado mediante Next.js BFF: no persistir access tokens en `localStorage` ni exponer claves secretas en variables `NEXT_PUBLIC_*`.
- Selector de empresa, logo/colores de agencia, resumen por organización y ficha de inmuebles tenant-scoped.
- Renderizar 401/403/404 y cambios de membresía correctamente. No usar datos ajenos ni enlaces directos a almacenamiento.
- Interfaz móvil orientada a asesores que publican por WhatsApp/Instagram (sin automatizar envíos todavía).

**Prompt para pegar:**

```text
Eres Frontend Engineer. CRM RAH VZLA será una plataforma para cualquier inmobiliaria de Venezuela. Lee CONTRACTS.md y docs/CONTRATO_API_V2_PROPUESTO.md. Trabaja SOLO frontend/. Integra flujo OIDC/BFF acordado, selector de inmobiliaria accesible, marca por organización y vistas de inmuebles que consumen la API v2 bajo /organizaciones/{org_id}. Los datos no pueden mezclarse entre agencias ni persistirse de una a otra tras cambiar el selector. Incluye pruebas E2E de cambio de organización, 401/403/404, móvil y estados vacíos. No inventes endpoints ni guardes tokens en localStorage. No toques backend/templates.
```

## Integrador humano (no delegar conflicto entre agentes)

1. Fijar contrato API v2 y naming antes de lanzar tres terminales.
2. Usar ramas/worktrees, no tres terminales editando los mismos archivos compartidos.
3. Revisar PR de esquema/identidad primero; fusionar backend y frontend después.
4. Ejecutar matriz completa de seguridad sobre Docker y guardar salida real.
5. No pasar a Sprint 03 (fábrica de contenido con marca de cada agencia) hasta terminar aislamiento.

## Fuera del Sprint 02

- Pago de suscripciones y cobros dentro de Venezuela.
- Planos 3D, contratos legales generados, portales y APIs de Meta o WhatsApp Business.
- Compartir inventario entre inmobiliarias.
- Vesty Assistant con acceso a datos reales, Skills/ECC desplegados con el producto.
