# Seguridad y comercialización · pendientes obligatorios

No subir datos reales ni exponer los puertos hasta resolver:

1. Autenticación (sesiones seguras), autorización por rol y por agencia/inquilino.
2. Aislamiento de datos si varias inmobiliarias comparten la instancia.
3. Registros de auditoría y cambios de precio/estado, almacenamiento de secretos, backups verificables y restauración.
4. Evaluación jurídica del tratamiento de datos aplicable en Venezuela y en cualquier mercado al que se expanda (incluido RGPD si corresponde): finalidad, avisos a interesados, retención, acceso, proveedores y transferencias, con asesoría local.
5. Permisos de publicación de fotografías e inventarios; reglas distintas para imágenes originales de portales y creatividades redes sociales.
6. Contratos: modelos revisados por profesional jurídico y aprobación explícita antes de exportar o firmar.
7. Rate limits, revisión de subidas, HTTPS, antivirus/escaneo cuando corresponda, cabeceras seguras y monitoreo.
8. Licencias de música, tipografías, fotografía, assets 3D y software usado comercialmente.
9. Autorización contractual y técnica para publicar en cada portal, independiente de que exista un exportador JSON/XML.
10. Jobs de medios asíncronos con colas, aislamiento de procesos, límites de CPU/RAM, reintentos y seguimiento de estado.

11. **Multiinmobiliaria:** ninguna ruta pública de v1, aislamiento A/B en consultas SQL, caché, archivos y trabajos; escenarios de abuso por cambiar `organizacion_id`; revocación de membresía y comprobación RLS con usuario SQL sin bypass.
12. No afirmar cumplimiento o certificación sin pruebas y revisión jurídica; `RAH` es nombre provisional y debe revisarse su uso comercial si coincide con marcas ajenas.
