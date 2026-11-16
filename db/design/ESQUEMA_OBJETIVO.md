# Modelo relacional propuesto (v0.3; SOLO diseño)

```text
organizaciones (id PK, slug UNIQUE, nombre, estatus)
  ├─ membresias (id PK, organizacion_id FK, usuario_id FK, rol, estatus)
  ├─ sucursales (id PK, organizacion_id FK, nombre)
  ├─ marca_organizacion (organizacion_id PK/FK, logo_asset_id, colores)
  ├─ inmuebles (id PK, organizacion_id FK, referencia, datos inmueble, asignado_membresia_id)
  │    └─ inmueble_media (id PK, organizacion_id FK, inmueble_id FK compuesta)
  ├─ clientes (id PK, organizacion_id FK, contacto privado)
  ├─ oportunidades (id PK, organizacion_id FK, inmueble_id y cliente_id compuestos; FUTURO)
  ├─ publicaciones (id PK, organizacion_id FK, inmueble_id compuesta)
  ├─ contratos (id PK, organizacion_id FK, inmueble_id y clientes compuestas; FUTURO)
  └─ auditoria_eventos (id PK, organizacion_id FK, actor, evento, fecha)
usuarios (id PK, proveedor_auth, subject, email) -- identidad transversal, sin mezclar datos de agencias
```

## Restricciones críticas

- FK de imagen `(organizacion_id, inmueble_id)` referencia UNIQUE `(organizacion_id, id)` en inmuebles. Repetir patrón para contratos, publicaciones, oportunidades.
- Referencia `UNIQUE (organizacion_id, codigo_referencia)` WHERE `codigo_referencia IS NOT NULL`.
- Invitaciones a empresa no conceden acceso hasta aceptación y validación.
- Usuarios multiorganización tienen un único usuario global, **distintas membresías**. Nunca guardar un único `usuario.organizacion_id`.
- Secretos, credenciales OIDC y datos personales fuera de auditoría y logs.
- Los datos DEMO anteriores se asignarán explícitamente a una organización DEMO nueva por backfill verificado, no silenciosamente a una agencia real.

## Transición de datos (design de migración)

1. Backup comprobado y restauración de prueba.
2. Crear tablas organizaciones/usuarios/membresías y organización DEMO.
3. Agregar `organizacion_id` nullable a las tablas privadas existentes.
4. Backfill de registros DEMO con la organización DEMO y verificar el conteo por tabla.
5. Establecer NOT NULL y FK compuestas, crear índices y unicidad por tenant.
6. Crear rol runtime no privilegiado; activar RLS y políticas `USING`/`WITH CHECK` para cada tabla, verificar pool/transacción.
7. Desactivar endpoints v1 anónimos fuera del desarrollo local; encender v2 con autenticación.
8. Ejecutar matriz de pruebas A/B (incluidas consultas con tenant omitido, upload y URLs).
