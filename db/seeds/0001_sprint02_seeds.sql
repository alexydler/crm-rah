-- ============================================================================
-- CRM RAH VZLA · Semillas de Desarrollo Sprint 02 (Datos 100% Ficticios)
-- ============================================================================

BEGIN;

-- 1. Organizaciones DEMO
INSERT INTO organizaciones (id, slug, nombre_comercial, estatus, moneda_preferida)
VALUES
    ('11111111-1111-4111-8111-111111111111', 'demo-caracas', 'Inmobiliaria Caracas DEMO', 'activa', 'USD'),
    ('22222222-2222-4222-8222-222222222222', 'demo-valencia', 'Inmobiliaria Valencia DEMO', 'activa', 'USD')
ON CONFLICT (id) DO UPDATE
    SET nombre_comercial = EXCLUDED.nombre_comercial,
        slug = EXCLUDED.slug;

-- 2. Usuarios de prueba (alineados con Keycloak OIDC)
INSERT INTO usuarios (id, proveedor_auth, subject, email, nombre_completo, estado)
VALUES
    ('e0000000-0000-4000-8000-000000000001', 'keycloak', 'usuario-a', 'usuario-a@ejemplo.com', 'Asesor Caracas', 'activo'),
    ('e0000000-0000-4000-8000-000000000002', 'keycloak', 'usuario-b', 'usuario-b@ejemplo.com', 'Asesor Valencia', 'activo'),
    ('e0000000-0000-4000-8000-000000000003', 'keycloak', 'usuario-ab', 'usuario-ab@ejemplo.com', 'Gerente Dual', 'activo')
ON CONFLICT (id) DO UPDATE
    SET subject = EXCLUDED.subject,
        email = EXCLUDED.email;

-- 3. Membresías
-- usuario-a: solo Org Caracas (asesor)
-- usuario-b: solo Org Valencia (asesor)
-- usuario-ab: ambas organizaciones (gerente)
INSERT INTO membresias (id, organizacion_id, usuario_id, rol, estatus)
VALUES
    ('f0000000-0000-4000-8000-000000000001', '11111111-1111-4111-8111-111111111111', 'e0000000-0000-4000-8000-000000000001', 'asesor', 'activa'),
    ('f0000000-0000-4000-8000-000000000002', '22222222-2222-4222-8222-222222222222', 'e0000000-0000-4000-8000-000000000002', 'asesor', 'activa'),
    ('f0000000-0000-4000-8000-000000000003', '11111111-1111-4111-8111-111111111111', 'e0000000-0000-4000-8000-000000000003', 'gerente', 'activa'),
    ('f0000000-0000-4000-8000-000000000004', '22222222-2222-4222-8222-222222222222', 'e0000000-0000-4000-8000-000000000003', 'gerente', 'activa')
ON CONFLICT (organizacion_id, usuario_id) DO UPDATE
    SET rol = EXCLUDED.rol,
        estatus = EXCLUDED.estatus;

-- 4. Los 3 inmuebles DEMO asignados explícitamente a la Organización Caracas
INSERT INTO inmuebles (
    id, organizacion_id, titulo, tipo, operacion, precio, moneda,
    direccion, zona, estado_ve, municipio, parroquia, urbanizacion,
    codigo_referencia, m2_construidos, m2_parcela, habitaciones, banos,
    extras, descripcion, estado
)
VALUES
(
    'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1',
    '11111111-1111-4111-8111-111111111111',
    'DEMO · Apartamento en urbanización ficticia',
    'apartamento', 'venta', 85000.00, 'USD',
    NULL, 'Caracas · ubicación ficticia', 'Miranda', 'Baruta', NULL,
    'Urbanización DEMO', 'DEMO-RAH-001', 88.00, NULL, 3, 2,
    '{"estacionamientos": 2}', 'Propiedad de prueba; no representa un anuncio real.', 'borrador'
),
(
    'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa2',
    '11111111-1111-4111-8111-111111111111',
    'DEMO · Quinta con patio',
    'quinta', 'venta', 130000.00, 'USD',
    NULL, 'Valencia · ubicación ficticia', 'Carabobo', 'Valencia', NULL,
    'Sector DEMO', 'DEMO-RAH-002', 160.00, 280.00, 4, 3,
    '{"patio": true}', 'Propiedad de prueba; no representa un anuncio real.', 'borrador'
),
(
    'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa3',
    '11111111-1111-4111-8111-111111111111',
    'DEMO · Galpón de prueba',
    'galpon', 'alquiler', 2500.00, 'USD',
    NULL, 'Maracaibo · ubicación ficticia', 'Zulia', 'Maracaibo', NULL,
    'Zona industrial DEMO', 'DEMO-RAH-003', 540.00, 630.00, NULL, 2,
    '{"uso": "comercial por verificar"}', 'Propiedad de prueba; no representa un anuncio real.', 'borrador'
)
ON CONFLICT (id) DO UPDATE
    SET organizacion_id = EXCLUDED.organizacion_id,
        titulo = EXCLUDED.titulo,
        precio = EXCLUDED.precio;

-- 5. Inmueble de prueba para Organización Valencia
-- Nota: Utiliza el mismo codigo_referencia DEMO-RAH-001 para verificar que la unicidad por organización funciona
INSERT INTO inmuebles (
    id, organizacion_id, titulo, tipo, operacion, precio, moneda,
    direccion, zona, estado_ve, municipio, parroquia, urbanizacion,
    codigo_referencia, m2_construidos, m2_parcela, habitaciones, banos,
    extras, descripcion, estado
)
VALUES
(
    'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbb1',
    '22222222-2222-4222-8222-222222222222',
    'DEMO · Local comercial en Valencia Centro',
    'local', 'venta', 60000.00, 'USD',
    NULL, 'Valencia · Centro ficticio', 'Carabobo', 'Valencia', NULL,
    'Casco Central DEMO', 'DEMO-RAH-001', 95.00, NULL, 1, 1,
    '{"vitrina": true}', 'Propiedad de prueba Valencia; no representa un anuncio real.', 'borrador'
)
ON CONFLICT (id) DO UPDATE
    SET organizacion_id = EXCLUDED.organizacion_id,
        titulo = EXCLUDED.titulo,
        precio = EXCLUDED.precio;

COMMIT;
