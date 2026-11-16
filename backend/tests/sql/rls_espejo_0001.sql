-- ESPEJO DE PRUEBA de las políticas RLS de db/migrations/0001_sprint02_multiagencia.sql
-- (rama sprint02-db, commit 7994e89). NO es la migración. Si la migración cambia, actualizar aquí
-- o, mejor, ejecutar las pruebas con TEST_SCHEMA_SQL apuntando a los SQL reales (ver conftest).

ALTER TABLE inmuebles ENABLE ROW LEVEL SECURITY;
ALTER TABLE inmuebles FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_inmuebles ON inmuebles AS PERMISSIVE FOR ALL TO PUBLIC
  USING (organizacion_id = NULLIF(current_setting('app.organizacion_id', true), '')::uuid)
  WITH CHECK (organizacion_id = NULLIF(current_setting('app.organizacion_id', true), '')::uuid);

ALTER TABLE inmueble_media ENABLE ROW LEVEL SECURITY;
ALTER TABLE inmueble_media FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_inmueble_media ON inmueble_media AS PERMISSIVE FOR ALL TO PUBLIC
  USING (organizacion_id = NULLIF(current_setting('app.organizacion_id', true), '')::uuid)
  WITH CHECK (organizacion_id = NULLIF(current_setting('app.organizacion_id', true), '')::uuid);

ALTER TABLE membresias ENABLE ROW LEVEL SECURITY;
ALTER TABLE membresias FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_membresias ON membresias AS PERMISSIVE FOR ALL TO PUBLIC
  USING (organizacion_id = NULLIF(current_setting('app.organizacion_id', true), '')::uuid)
  WITH CHECK (organizacion_id = NULLIF(current_setting('app.organizacion_id', true), '')::uuid);

ALTER TABLE organizaciones ENABLE ROW LEVEL SECURITY;
ALTER TABLE organizaciones FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_organizaciones ON organizaciones AS PERMISSIVE FOR ALL TO PUBLIC
  USING (id = NULLIF(current_setting('app.organizacion_id', true), '')::uuid)
  WITH CHECK (id = NULLIF(current_setting('app.organizacion_id', true), '')::uuid);
