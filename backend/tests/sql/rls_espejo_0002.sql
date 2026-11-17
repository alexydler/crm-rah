-- ESPEJO DE PRUEBA de db/migrations/0002_rls_usuario_lectura.sql (sprint02-db, c8f7581).
-- Políticas PERMISSIVE de solo lectura: cada usuario ve sus propias membresías y organizaciones
-- según app.usuario_sub (sub del token ya verificado). Se combinan con OR con las de tenant.

CREATE POLICY membresias_propias_lectura ON membresias AS PERMISSIVE FOR SELECT TO PUBLIC
  USING (usuario_id IN (
    SELECT u.id FROM usuarios u
    WHERE u.subject = NULLIF(current_setting('app.usuario_sub', true), '')
  ));

CREATE POLICY organizaciones_propias_lectura ON organizaciones AS PERMISSIVE FOR SELECT TO PUBLIC
  USING (id IN (
    SELECT m.organizacion_id FROM membresias m JOIN usuarios u ON u.id = m.usuario_id
    WHERE u.subject = NULLIF(current_setting('app.usuario_sub', true), '')
  ));
