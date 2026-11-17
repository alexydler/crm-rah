-- ============================================================================
-- CRM RAH VZLA · Rollback Migración 0002
-- ============================================================================

BEGIN;

DROP POLICY IF EXISTS membresias_propias_lectura ON membresias;
DROP POLICY IF EXISTS organizaciones_propias_lectura ON organizaciones;

DELETE FROM alembic_version WHERE version_num = '0002_rls_usuario_lectura';
INSERT INTO alembic_version (version_num) VALUES ('0001_sprint02_multiagencia');

COMMIT;
