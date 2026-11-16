-- PROPUESTA PARA EL DBA (no existe aún en la migración 0001).
--
-- Problema: con RLS por organización en `membresias` y `organizaciones`, el backend no puede
-- (a) verificar la membresía ANTES de fijar app.organizacion_id, ni (b) listar las organizaciones
-- del usuario en GET /api/v2/me y /api/v2/organizaciones. Fijar el org de la URL antes de
-- verificar sería usar un dato del cliente como contexto previo a la autorización.
--
-- Solución: políticas PERMISSIVE adicionales SOLO DE LECTURA que muestran al usuario sus propias
-- membresías y organizaciones. El backend fija app.usuario_sub (sub del token ya verificado)
-- con set_config(..., true) antes de esas consultas. Las políticas se combinan con OR con las de
-- tenant; no conceden INSERT/UPDATE/DELETE ni filas de otros usuarios.

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
