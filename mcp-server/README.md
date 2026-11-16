# Servidor MCP — fase futura

No se entrega un servidor MCP ficticio en el MVP. Primero se validan el esquema, los permisos y la API. La siguiente fase añade herramientas de **lectura de inmuebles** y generación de **borradores** con permisos explícitos.

Al desplegarlo: acceso mínimo, lista blanca de funciones, autenticación, confirmación para escribir/publicar, registro de auditoría; no exponer PostgreSQL ni claves MinIO directamente a un modelo.
