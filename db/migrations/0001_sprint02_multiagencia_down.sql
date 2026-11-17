-- ============================================================================
-- CRM RAH VZLA · Rollback Migración Sprint 02
-- ============================================================================

BEGIN;

-- 1. Eliminar políticas y deshabilitar RLS
DROP POLICY IF EXISTS tenant_isolation_inmuebles ON inmuebles;
ALTER TABLE inmuebles NO FORCE ROW LEVEL SECURITY;
ALTER TABLE inmuebles DISABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS tenant_isolation_inmueble_media ON inmueble_media;
ALTER TABLE inmueble_media NO FORCE ROW LEVEL SECURITY;
ALTER TABLE inmueble_media DISABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS tenant_isolation_membresias ON membresias;
ALTER TABLE membresias NO FORCE ROW LEVEL SECURITY;
ALTER TABLE membresias DISABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS tenant_isolation_organizaciones ON organizaciones;
ALTER TABLE organizaciones NO FORCE ROW LEVEL SECURITY;
ALTER TABLE organizaciones DISABLE ROW LEVEL SECURITY;

DO $$
BEGIN
    IF EXISTS (SELECT FROM pg_tables WHERE tablename = 'clientes') THEN
        DROP POLICY IF EXISTS tenant_isolation_clientes ON clientes;
        ALTER TABLE clientes NO FORCE ROW LEVEL SECURITY;
        ALTER TABLE clientes DISABLE ROW LEVEL SECURITY;
    END IF;

    IF EXISTS (SELECT FROM pg_tables WHERE tablename = 'contratos') THEN
        DROP POLICY IF EXISTS tenant_isolation_contratos ON contratos;
        ALTER TABLE contratos NO FORCE ROW LEVEL SECURITY;
        ALTER TABLE contratos DISABLE ROW LEVEL SECURITY;
    END IF;

    IF EXISTS (SELECT FROM pg_tables WHERE tablename = 'publicaciones') THEN
        DROP POLICY IF EXISTS tenant_isolation_publicaciones ON publicaciones;
        ALTER TABLE publicaciones NO FORCE ROW LEVEL SECURITY;
        ALTER TABLE publicaciones DISABLE ROW LEVEL SECURITY;
    END IF;
END $$;

-- 2. Revertir inmueble_media
DROP INDEX IF EXISTS idx_media_org_inmueble;
ALTER TABLE inmueble_media DROP CONSTRAINT IF EXISTS fk_media_inmueble_org;
ALTER TABLE inmueble_media
    ADD CONSTRAINT inmueble_media_inmueble_id_fkey
    FOREIGN KEY (inmueble_id) REFERENCES inmuebles (id) ON DELETE CASCADE;
ALTER TABLE inmueble_media DROP COLUMN IF EXISTS organizacion_id;

-- 3. Revertir inmuebles
DROP INDEX IF EXISTS idx_inmuebles_org_codigo_referencia;
CREATE UNIQUE INDEX IF NOT EXISTS idx_inmuebles_codigo_referencia
    ON inmuebles (codigo_referencia)
    WHERE codigo_referencia IS NOT NULL;
ALTER TABLE inmuebles DROP CONSTRAINT IF EXISTS uq_inmuebles_org_id;
ALTER TABLE inmuebles DROP CONSTRAINT IF EXISTS fk_inmuebles_organizacion;
ALTER TABLE inmuebles DROP COLUMN IF EXISTS organizacion_id;

-- 4. Revertir tablas preparadas
DO $$
BEGIN
    IF EXISTS (SELECT FROM pg_tables WHERE tablename = 'clientes') THEN
        ALTER TABLE clientes DROP CONSTRAINT IF EXISTS uq_clientes_org_id;
        ALTER TABLE clientes DROP CONSTRAINT IF EXISTS fk_clientes_organizacion;
        ALTER TABLE clientes DROP COLUMN IF EXISTS organizacion_id;
    END IF;

    IF EXISTS (SELECT FROM pg_tables WHERE tablename = 'contratos') THEN
        ALTER TABLE contratos DROP CONSTRAINT IF EXISTS fk_contratos_organizacion;
        ALTER TABLE contratos DROP COLUMN IF EXISTS organizacion_id;
    END IF;

    IF EXISTS (SELECT FROM pg_tables WHERE tablename = 'publicaciones') THEN
        ALTER TABLE publicaciones DROP CONSTRAINT IF EXISTS fk_publicaciones_organizacion;
        ALTER TABLE publicaciones DROP COLUMN IF EXISTS organizacion_id;
    END IF;
END $$;

-- 5. Eliminar tablas del Sprint 02
DROP TABLE IF EXISTS membresias CASCADE;
DROP TABLE IF EXISTS usuarios CASCADE;
DROP TABLE IF EXISTS organizaciones CASCADE;

DELETE FROM alembic_version WHERE version_num = '0001_sprint02_multiagencia';

COMMIT;
