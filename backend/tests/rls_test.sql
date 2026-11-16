-- ESPEJO DE PRUEBA de las políticas RLS esperadas (NO es la migración; la entrega el DBA en db/).
-- La app fija app.organizacion_id con set_config(..., true) (= SET LOCAL) por transacción.
-- Sin contexto, current_setting(..., true) es NULL o '' → ninguna fila visible ni insertable.

GRANT USAGE ON SCHEMA public TO :app_role;
GRANT SELECT ON organizaciones TO :app_role;
GRANT SELECT, UPDATE ON membresias TO :app_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON inmuebles, inmueble_media TO :app_role;

ALTER TABLE inmuebles ENABLE ROW LEVEL SECURITY;
ALTER TABLE inmuebles FORCE ROW LEVEL SECURITY;
ALTER TABLE inmueble_media ENABLE ROW LEVEL SECURITY;
ALTER TABLE inmueble_media FORCE ROW LEVEL SECURITY;

CREATE POLICY inmuebles_tenant ON inmuebles
  USING (organizacion_id = NULLIF(current_setting('app.organizacion_id', true), '')::uuid)
  WITH CHECK (organizacion_id = NULLIF(current_setting('app.organizacion_id', true), '')::uuid);

CREATE POLICY inmueble_media_tenant ON inmueble_media
  USING (organizacion_id = NULLIF(current_setting('app.organizacion_id', true), '')::uuid)
  WITH CHECK (organizacion_id = NULLIF(current_setting('app.organizacion_id', true), '')::uuid);

-- membresias/organizaciones sin RLS por organización en este espejo: la app debe leer la
-- membresía ANTES de conocer la org verificada. Si el DBA añade RLS por usuario, la app ya fija
-- app.usuario_sub antes de esa consulta.
