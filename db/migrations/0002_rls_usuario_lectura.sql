-- ============================================================================
-- CRM RAH VZLA · Migración 0002: RLS de Lectura por Usuario (app.usuario_sub)
-- ============================================================================

BEGIN;

DROP POLICY IF EXISTS membresias_propias_lectura ON membresias;
CREATE POLICY membresias_propias_lectura ON membresias
    AS PERMISSIVE FOR SELECT
    TO PUBLIC
    USING (usuario_id IN (
        SELECT u.id FROM usuarios u
        WHERE u.subject = NULLIF(current_setting('app.usuario_sub', true), '')
    ));

DROP POLICY IF EXISTS organizaciones_propias_lectura ON organizaciones;
CREATE POLICY organizaciones_propias_lectura ON organizaciones
    AS PERMISSIVE FOR SELECT
    TO PUBLIC
    USING (id IN (
        SELECT m.organizacion_id FROM membresias m JOIN usuarios u ON u.id = m.usuario_id
        WHERE u.subject = NULLIF(current_setting('app.usuario_sub', true), '')
    ));

-- Actualizar versión en alembic_version si existe
CREATE TABLE IF NOT EXISTS alembic_version (
    version_num VARCHAR(32) NOT NULL,
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);
DELETE FROM alembic_version;
INSERT INTO alembic_version (version_num) VALUES ('0002_rls_usuario_lectura');

COMMIT;
