-- ============================================================================
-- CRM RAH VZLA · Migración Sprint 02 (Multiinmobiliaria, RLS, Rol de App)
-- Transaccional y Reversible
-- ============================================================================

BEGIN;

-- 1. Tabla organizaciones
CREATE TABLE IF NOT EXISTS organizaciones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    slug VARCHAR(80) NOT NULL UNIQUE,
    nombre_comercial VARCHAR(160) NOT NULL,
    estatus VARCHAR(20) NOT NULL DEFAULT 'activa' CHECK (estatus IN ('activa', 'suspendida', 'inactiva')),
    moneda_preferida CHAR(3) NOT NULL DEFAULT 'USD' CHECK (moneda_preferida IN ('USD', 'VES')),
    creado_en TIMESTAMPTZ NOT NULL DEFAULT now(),
    actualizado_en TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 2. Tabla usuarios y membresias
CREATE TABLE IF NOT EXISTS usuarios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    proveedor_auth VARCHAR(40) NOT NULL DEFAULT 'keycloak',
    subject VARCHAR(120) NOT NULL UNIQUE,
    email VARCHAR(160) NOT NULL UNIQUE,
    nombre_completo VARCHAR(160),
    estado VARCHAR(20) NOT NULL DEFAULT 'activo' CHECK (estado IN ('activo', 'inactivo', 'bloqueado')),
    creado_en TIMESTAMPTZ NOT NULL DEFAULT now(),
    actualizado_en TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS membresias (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organizacion_id UUID NOT NULL REFERENCES organizaciones(id) ON DELETE CASCADE,
    usuario_id UUID NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    rol VARCHAR(30) NOT NULL CHECK (rol IN ('propietario', 'gerente', 'asesor', 'marketing', 'consulta')),
    estatus VARCHAR(20) NOT NULL DEFAULT 'activa' CHECK (estatus IN ('activa', 'inactiva', 'invitado')),
    creado_en TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_membresias_org_usuario UNIQUE (organizacion_id, usuario_id)
);
CREATE INDEX IF NOT EXISTS idx_membresias_org_usuario ON membresias(organizacion_id, usuario_id);

-- 3. Semillas base para migración / backfill (Caracas y Valencia)
INSERT INTO organizaciones (id, slug, nombre_comercial, estatus, moneda_preferida)
VALUES
    ('11111111-1111-4111-8111-111111111111', 'demo-caracas', 'Inmobiliaria Caracas DEMO', 'activa', 'USD'),
    ('22222222-2222-4222-8222-222222222222', 'demo-valencia', 'Inmobiliaria Valencia DEMO', 'activa', 'USD')
ON CONFLICT (id) DO UPDATE
    SET nombre_comercial = EXCLUDED.nombre_comercial,
        slug = EXCLUDED.slug;

INSERT INTO usuarios (id, proveedor_auth, subject, email, nombre_completo, estado)
VALUES
    ('e0000000-0000-4000-8000-000000000001', 'keycloak', 'usuario-a', 'usuario-a@ejemplo.com', 'Asesor Caracas', 'activo'),
    ('e0000000-0000-4000-8000-000000000002', 'keycloak', 'usuario-b', 'usuario-b@ejemplo.com', 'Asesor Valencia', 'activo'),
    ('e0000000-0000-4000-8000-000000000003', 'keycloak', 'usuario-ab', 'usuario-ab@ejemplo.com', 'Gerente Dual', 'activo')
ON CONFLICT (id) DO NOTHING;

INSERT INTO membresias (id, organizacion_id, usuario_id, rol, estatus)
VALUES
    ('f0000000-0000-4000-8000-000000000001', '11111111-1111-4111-8111-111111111111', 'e0000000-0000-4000-8000-000000000001', 'asesor', 'activa'),
    ('f0000000-0000-4000-8000-000000000002', '22222222-2222-4222-8222-222222222222', 'e0000000-0000-4000-8000-000000000002', 'asesor', 'activa'),
    ('f0000000-0000-4000-8000-000000000003', '11111111-1111-4111-8111-111111111111', 'e0000000-0000-4000-8000-000000000003', 'gerente', 'activa'),
    ('f0000000-0000-4000-8000-000000000004', '22222222-2222-4222-8222-222222222222', 'e0000000-0000-4000-8000-000000000003', 'gerente', 'activa')
ON CONFLICT (organizacion_id, usuario_id) DO NOTHING;

-- 4. Modificar inmuebles: organizacion_id NOT NULL, FK, UNIQUE (organizacion_id, id)
ALTER TABLE inmuebles ADD COLUMN IF NOT EXISTS organizacion_id UUID;

-- Backfill verificado: asignar inmuebles existentes sin tenant a la org DEMO Caracas
UPDATE inmuebles
SET organizacion_id = '11111111-1111-4111-8111-111111111111'
WHERE organizacion_id IS NULL;

ALTER TABLE inmuebles ALTER COLUMN organizacion_id SET NOT NULL;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'fk_inmuebles_organizacion'
    ) THEN
        ALTER TABLE inmuebles
            ADD CONSTRAINT fk_inmuebles_organizacion
            FOREIGN KEY (organizacion_id) REFERENCES organizaciones(id) ON DELETE CASCADE;
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'uq_inmuebles_org_id'
    ) THEN
        ALTER TABLE inmuebles ADD CONSTRAINT uq_inmuebles_org_id UNIQUE (organizacion_id, id);
    END IF;
END $$;

DROP INDEX IF EXISTS idx_inmuebles_codigo_referencia;
CREATE UNIQUE INDEX IF NOT EXISTS idx_inmuebles_org_codigo_referencia
    ON inmuebles (organizacion_id, codigo_referencia)
    WHERE codigo_referencia IS NOT NULL;

-- 5. Modificar inmueble_media: organizacion_id NOT NULL, FK compuesta e índice
ALTER TABLE inmueble_media ADD COLUMN IF NOT EXISTS organizacion_id UUID;

UPDATE inmueble_media m
SET organizacion_id = i.organizacion_id
FROM inmuebles i
WHERE m.inmueble_id = i.id AND m.organizacion_id IS NULL;

UPDATE inmueble_media
SET organizacion_id = '11111111-1111-4111-8111-111111111111'
WHERE organizacion_id IS NULL;

ALTER TABLE inmueble_media ALTER COLUMN organizacion_id SET NOT NULL;

ALTER TABLE inmueble_media DROP CONSTRAINT IF EXISTS inmueble_media_inmueble_id_fkey;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'fk_media_inmueble_org'
    ) THEN
        ALTER TABLE inmueble_media
            ADD CONSTRAINT fk_media_inmueble_org
            FOREIGN KEY (organizacion_id, inmueble_id)
            REFERENCES inmuebles (organizacion_id, id) ON DELETE CASCADE;
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_media_org_inmueble
    ON inmueble_media (organizacion_id, inmueble_id, orden);

-- 6. Tablas adicionales: clientes, contratos, publicaciones (si existen)
DO $$
BEGIN
    IF EXISTS (SELECT FROM pg_tables WHERE tablename = 'clientes') THEN
        ALTER TABLE clientes ADD COLUMN IF NOT EXISTS organizacion_id UUID;
        UPDATE clientes SET organizacion_id = '11111111-1111-4111-8111-111111111111' WHERE organizacion_id IS NULL;
        ALTER TABLE clientes ALTER COLUMN organizacion_id SET NOT NULL;
        IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_clientes_organizacion') THEN
            ALTER TABLE clientes ADD CONSTRAINT fk_clientes_organizacion FOREIGN KEY (organizacion_id) REFERENCES organizaciones(id) ON DELETE CASCADE;
        END IF;
        IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_clientes_org_id') THEN
            ALTER TABLE clientes ADD CONSTRAINT uq_clientes_org_id UNIQUE (organizacion_id, id);
        END IF;
    END IF;

    IF EXISTS (SELECT FROM pg_tables WHERE tablename = 'contratos') THEN
        ALTER TABLE contratos ADD COLUMN IF NOT EXISTS organizacion_id UUID;
        UPDATE contratos SET organizacion_id = '11111111-1111-4111-8111-111111111111' WHERE organizacion_id IS NULL;
        ALTER TABLE contratos ALTER COLUMN organizacion_id SET NOT NULL;
        IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_contratos_organizacion') THEN
            ALTER TABLE contratos ADD CONSTRAINT fk_contratos_organizacion FOREIGN KEY (organizacion_id) REFERENCES organizaciones(id) ON DELETE CASCADE;
        END IF;
    END IF;

    IF EXISTS (SELECT FROM pg_tables WHERE tablename = 'publicaciones') THEN
        ALTER TABLE publicaciones ADD COLUMN IF NOT EXISTS organizacion_id UUID;
        UPDATE publicaciones SET organizacion_id = '11111111-1111-4111-8111-111111111111' WHERE organizacion_id IS NULL;
        ALTER TABLE publicaciones ALTER COLUMN organizacion_id SET NOT NULL;
        IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_publicaciones_organizacion') THEN
            ALTER TABLE publicaciones ADD CONSTRAINT fk_publicaciones_organizacion FOREIGN KEY (organizacion_id) REFERENCES organizaciones(id) ON DELETE CASCADE;
        END IF;
    END IF;
END $$;

-- 7. Crear rol de aplicación sin BYPASSRLS y no-owner
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'rah_app') THEN
        CREATE ROLE rah_app WITH LOGIN PASSWORD 'dev_only_change_me_app'
            NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS;
    ELSE
        ALTER ROLE rah_app WITH NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS;
    END IF;
END $$;

GRANT USAGE ON SCHEMA public TO rah_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO rah_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO rah_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO rah_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO rah_app;

-- 8. Activar Row Level Security (RLS) en todas las tablas privadas
ALTER TABLE inmuebles ENABLE ROW LEVEL SECURITY;
ALTER TABLE inmuebles FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS tenant_isolation_inmuebles ON inmuebles;
CREATE POLICY tenant_isolation_inmuebles ON inmuebles
    AS PERMISSIVE FOR ALL
    TO PUBLIC
    USING (organizacion_id = NULLIF(current_setting('app.organizacion_id', true), '')::uuid)
    WITH CHECK (organizacion_id = NULLIF(current_setting('app.organizacion_id', true), '')::uuid);

ALTER TABLE inmueble_media ENABLE ROW LEVEL SECURITY;
ALTER TABLE inmueble_media FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS tenant_isolation_inmueble_media ON inmueble_media;
CREATE POLICY tenant_isolation_inmueble_media ON inmueble_media
    AS PERMISSIVE FOR ALL
    TO PUBLIC
    USING (organizacion_id = NULLIF(current_setting('app.organizacion_id', true), '')::uuid)
    WITH CHECK (organizacion_id = NULLIF(current_setting('app.organizacion_id', true), '')::uuid);

ALTER TABLE membresias ENABLE ROW LEVEL SECURITY;
ALTER TABLE membresias FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS tenant_isolation_membresias ON membresias;
CREATE POLICY tenant_isolation_membresias ON membresias
    AS PERMISSIVE FOR ALL
    TO PUBLIC
    USING (organizacion_id = NULLIF(current_setting('app.organizacion_id', true), '')::uuid)
    WITH CHECK (organizacion_id = NULLIF(current_setting('app.organizacion_id', true), '')::uuid);

ALTER TABLE organizaciones ENABLE ROW LEVEL SECURITY;
ALTER TABLE organizaciones FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS tenant_isolation_organizaciones ON organizaciones;
CREATE POLICY tenant_isolation_organizaciones ON organizaciones
    AS PERMISSIVE FOR ALL
    TO PUBLIC
    USING (id = NULLIF(current_setting('app.organizacion_id', true), '')::uuid)
    WITH CHECK (id = NULLIF(current_setting('app.organizacion_id', true), '')::uuid);

DO $$
BEGIN
    IF EXISTS (SELECT FROM pg_tables WHERE tablename = 'clientes') THEN
        ALTER TABLE clientes ENABLE ROW LEVEL SECURITY;
        ALTER TABLE clientes FORCE ROW LEVEL SECURITY;
        DROP POLICY IF EXISTS tenant_isolation_clientes ON clientes;
        CREATE POLICY tenant_isolation_clientes ON clientes
            AS PERMISSIVE FOR ALL
            TO PUBLIC
            USING (organizacion_id = NULLIF(current_setting('app.organizacion_id', true), '')::uuid)
            WITH CHECK (organizacion_id = NULLIF(current_setting('app.organizacion_id', true), '')::uuid);
    END IF;

    IF EXISTS (SELECT FROM pg_tables WHERE tablename = 'contratos') THEN
        ALTER TABLE contratos ENABLE ROW LEVEL SECURITY;
        ALTER TABLE contratos FORCE ROW LEVEL SECURITY;
        DROP POLICY IF EXISTS tenant_isolation_contratos ON contratos;
        CREATE POLICY tenant_isolation_contratos ON contratos
            AS PERMISSIVE FOR ALL
            TO PUBLIC
            USING (organizacion_id = NULLIF(current_setting('app.organizacion_id', true), '')::uuid)
            WITH CHECK (organizacion_id = NULLIF(current_setting('app.organizacion_id', true), '')::uuid);
    END IF;

    IF EXISTS (SELECT FROM pg_tables WHERE tablename = 'publicaciones') THEN
        ALTER TABLE publicaciones ENABLE ROW LEVEL SECURITY;
        ALTER TABLE publicaciones FORCE ROW LEVEL SECURITY;
        DROP POLICY IF EXISTS tenant_isolation_publicaciones ON publicaciones;
        CREATE POLICY tenant_isolation_publicaciones ON publicaciones
            AS PERMISSIVE FOR ALL
            TO PUBLIC
            USING (organizacion_id = NULLIF(current_setting('app.organizacion_id', true), '')::uuid)
            WITH CHECK (organizacion_id = NULLIF(current_setting('app.organizacion_id', true), '')::uuid);
    END IF;
END $$;

-- Registrar versión en alembic_version si la tabla existe
CREATE TABLE IF NOT EXISTS alembic_version (
    version_num VARCHAR(32) NOT NULL,
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);
DELETE FROM alembic_version;
INSERT INTO alembic_version (version_num) VALUES ('0001_sprint02_multiagencia');

COMMIT;
