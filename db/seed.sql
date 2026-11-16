-- Datos completamente inventados para pruebas: NO anuncios reales ni propiedades RAH.
INSERT INTO inmuebles (id,titulo,tipo,operacion,precio,moneda,direccion,zona,estado_ve,municipio,parroquia,urbanizacion,codigo_referencia,m2_construidos,m2_parcela,habitaciones,banos,extras,descripcion,estado)
VALUES
('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1','DEMO · Apartamento en urbanización ficticia','apartamento','venta',85000,'USD',NULL,'Caracas · ubicación ficticia','Miranda','Baruta',NULL,'Urbanización DEMO','DEMO-RAH-001',88,NULL,3,2,'{"estacionamientos":2}', 'Propiedad de prueba; no representa un anuncio real.', 'borrador'),
('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa2','DEMO · Quinta con patio','quinta','venta',130000,'USD',NULL,'Valencia · ubicación ficticia','Carabobo','Valencia',NULL,'Sector DEMO','DEMO-RAH-002',160,280,4,3,'{"patio":true}', 'Propiedad de prueba; no representa un anuncio real.', 'borrador'),
('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa3','DEMO · Galpón de prueba','galpon','alquiler',2500,'USD',NULL,'Maracaibo · ubicación ficticia','Zulia','Maracaibo',NULL,'Zona industrial DEMO','DEMO-RAH-003',540,630,NULL,2,'{"uso":"comercial por verificar"}', 'Propiedad de prueba; no representa un anuncio real.', 'borrador')
ON CONFLICT (id) DO NOTHING;
