# Contrato de API v2 propuesto · multiinmobiliaria

**Estado:** PROPUESTA CONTRACTUAL para Sprint 02. No implementado. No confundir con los endpoints v1 sin autenticación del prototipo.

## Reglas transversales

- Rutas privadas: `/api/v2/organizaciones/{organizacion_id}/...` (UUID).
- La identidad llega de un sistema OIDC validado por servidor; **no** confiar en `X-Organization-ID` ni en `organizacion_id` del JSON de entrada como autorización.
- Verificar membresía activa para esa organización y el rol/permiso de cada endpoint. Control por recurso adicional para datos asignados a asesores.
- Respuestas JSON, UUID, precio decimal como string, fechas ISO 8601 UTC, idioma español; la moneda no se convierte automáticamente entre USD/VES.
- `401`: no autenticado; `403`: no tiene permiso dentro de su organización; `404`: registro no existente o ajeno a la organización; `409`: referencia duplicada **dentro de la misma organización**; `422`: validación.
- Medios privados con URL firmada solo tras verificar `organizacion_id`, `inmueble_id` y pertenencia del asset.
- `organizacion_id` y `creado_por` son valores del servidor, NUNCA aceptados del cliente en operaciones ordinarias.
- API v1 del prototipo debe quedar deshabilitada / solo localhost y datos DEMO hasta completar el sprint. Nada de migrar a producción con v1 accesible.

## Identidad y organización

| Método | Ruta | Permiso / resultado |
| --- | --- | --- |
| GET | `/api/v2/me` | Usuario autenticado y membresías activas (sin datos de terceros) |
| GET | `/api/v2/me/organizaciones` | Organizaciones a las que pertenece |
| GET | `/api/v2/organizaciones/{org_id}` | Miembro activo de esa organización |
| PATCH | `/api/v2/organizaciones/{org_id}/marca` | Propietario, actualiza identidad visual |
| GET | `/api/v2/organizaciones/{org_id}/marca` | Miembro con permiso de visualización |
| POST | `/api/v2/organizaciones/{org_id}/invitaciones` | Propietario, crea invitación con rol permitido (posterior al primer corte seguro) |

## Inmuebles

| Método | Ruta | Resultado |
| --- | --- | --- |
| GET | `/api/v2/organizaciones/{org_id}/inmuebles?tipo=&estado=` | Solo inmuebles visibles para ese usuario |
| POST | `/api/v2/organizaciones/{org_id}/inmuebles` | 201, inmueble creado bajo org validada |
| GET | `/api/v2/organizaciones/{org_id}/inmuebles/{inmueble_id}` | Ficha de esa organización o 404 |
| PATCH | `/api/v2/organizaciones/{org_id}/inmuebles/{inmueble_id}` | Actualiza campos permitidos; registrar auditoría |
| GET | `/api/v2/organizaciones/{org_id}/inmuebles/{inmueble_id}/media` | Lista autorizada de medios y URLs temporales |
| POST | `/api/v2/organizaciones/{org_id}/inmuebles/{inmueble_id}/media` | Sube medio privado, valida MIME y tamaño |

## Inmueble v2 (ejemplo ficticio)

```json
{
  "id": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1",
  "organizacion_id": "11111111-1111-4111-8111-111111111111",
  "codigo_referencia": "VAL-001",
  "titulo": "DEMO - apartamento ficticio",
  "tipo": "apartamento",
  "operacion": "venta",
  "precio": "85000.00",
  "moneda": "USD",
  "estado_ve": "Carabobo",
  "municipio": "Valencia",
  "parroquia": null,
  "urbanizacion": "Sector ficticio",
  "zona": "Zona ficticia",
  "estado": "borrador"
}
```

El POST omite `id` y `organizacion_id`. El servidor los asigna. Dos organizaciones distintas pueden tener la referencia `VAL-001` sin conflicto.

## Marca de agencia (esquema inicial)

```json
{
  "nombre_publico": "Inmobiliaria DEMO A",
  "logo_asset_id": null,
  "color_primario": "#1B6C80",
  "color_secundario": "#FFFFFF",
  "whatsapp_comercial": null,
  "pie_publicaciones": "Información sujeta a verificación"
}
```

No imprimir teléfonos, direcciones privadas de clientes ni fotografías no autorizadas en creatividades. Para logo, usar archivo autorizado almacenado en privado.
