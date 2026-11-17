-- ============================================================================
-- CRM RAH VZLA · Suite de Validación Manual y Automatizada de RLS
-- Ejecutable con: psql -U rah_dev -d rah_vzla -f db/test_rls.sql
-- ============================================================================

\set ON_ERROR_STOP on

\echo '----------------------------------------------------------------------'
\echo 'INICIANDO PRUEBAS DE AISLAMIENTO MULTI-TENANT Y ROW LEVEL SECURITY (RLS)'
\echo '----------------------------------------------------------------------'

-- Cambiar al rol de aplicación (no privilegiado, sin BYPASSRLS)
SET ROLE rah_app;

\echo ''
\echo '>>> TEST 1: Consulta sin app.organizacion_id configurada (Debe retornar 0 filas)'
BEGIN;
SELECT count(*) AS total_filas_sin_tenant FROM inmuebles;
-- Verificación
DO $$
DECLARE
    cnt INT;
BEGIN
    SELECT count(*) INTO cnt FROM inmuebles;
    IF cnt <> 0 THEN
        RAISE EXCEPTION 'TEST 1 FALLÓ: Se esperaban 0 filas, se obtuvieron %', cnt;
    END IF;
    RAISE NOTICE 'TEST 1 SUPERADO: 0 filas devueltas sin contexto de tenant.';
END $$;
ROLLBACK;


\echo ''
\echo '>>> TEST 2: Contexto activo Organización Caracas (11111111-1111-4111-8111-111111111111)'
BEGIN;
SET LOCAL app.organizacion_id = '11111111-1111-4111-8111-111111111111';

SELECT id, codigo_referencia, titulo, organizacion_id FROM inmuebles;

DO $$
DECLARE
    cnt INT;
    otro_tenant INT;
BEGIN
    SELECT count(*) INTO cnt FROM inmuebles;
    SELECT count(*) INTO otro_tenant FROM inmuebles WHERE organizacion_id <> '11111111-1111-4111-8111-111111111111';

    IF cnt < 3 THEN
        RAISE EXCEPTION 'TEST 2 FALLÓ: Se esperaban al menos 3 inmuebles de Caracas, se obtuvieron %', cnt;
    END IF;
    IF otro_tenant > 0 THEN
        RAISE EXCEPTION 'TEST 2 FALLÓ: FUGA DE DATOS DETECTADA! Se devolvieron % filas de otras organizaciones', otro_tenant;
    END IF;
    RAISE NOTICE 'TEST 2 SUPERADO: % inmuebles de Caracas visibles, 0 fugas de otros tenants.', cnt;
END $$;
ROLLBACK;


\echo ''
\echo '>>> TEST 3: Contexto activo Organización Valencia (22222222-2222-4222-8222-222222222222)'
BEGIN;
SET LOCAL app.organizacion_id = '22222222-2222-4222-8222-222222222222';

SELECT id, codigo_referencia, titulo, organizacion_id FROM inmuebles;

DO $$
DECLARE
    cnt INT;
    otro_tenant INT;
BEGIN
    SELECT count(*) INTO cnt FROM inmuebles;
    SELECT count(*) INTO otro_tenant FROM inmuebles WHERE organizacion_id <> '22222222-2222-4222-8222-222222222222';

    IF cnt < 1 THEN
        RAISE EXCEPTION 'TEST 3 FALLÓ: Se esperaba al menos 1 inmueble de Valencia, se obtuvieron %', cnt;
    END IF;
    IF otro_tenant > 0 THEN
        RAISE EXCEPTION 'TEST 3 FALLÓ: FUGA DE DATOS DETECTADA! Se devolvieron % filas de Caracas', otro_tenant;
    END IF;
    RAISE NOTICE 'TEST 3 SUPERADO: % inmuebles de Valencia visibles, 0 fugas de Caracas.', cnt;
END $$;
ROLLBACK;


\echo ''
\echo '>>> TEST 4: Unicidad de codigo_referencia por organización (Ambas tienen DEMO-RAH-001)'
-- Volvemos a rol administrativo solo para consultar sin RLS el total de referencias
RESET ROLE;
DO $$
DECLARE
    cnt INT;
BEGIN
    SELECT count(*) INTO cnt FROM inmuebles WHERE codigo_referencia = 'DEMO-RAH-001';
    IF cnt < 2 THEN
        RAISE EXCEPTION 'TEST 4 FALLÓ: Se esperaba que DEMO-RAH-001 existiera en ambas organizaciones (cnt=%), pero no fue así', cnt;
    END IF;
    RAISE NOTICE 'TEST 4 SUPERADO: Codigo DEMO-RAH-001 existe simultáneamente en Caracas y Valencia sin colisión.';
END $$;


\echo ''
\echo '>>> TEST 5: Intento de Inserción Cruzada (Ataque Cross-Tenant bloqueado por WITH CHECK)'
SET ROLE rah_app;
BEGIN;
SET LOCAL app.organizacion_id = '11111111-1111-4111-8111-111111111111';

DO $$
BEGIN
    BEGIN
        INSERT INTO inmuebles (
            titulo, tipo, operacion, precio, moneda, zona, organizacion_id
        ) VALUES (
            'Ataque Cross Tenant', 'apartamento', 'venta', 50000, 'USD', 'Zona Test',
            '22222222-2222-4222-8222-222222222222' -- Intento de escribir en Valencia estando en sesión Caracas
        );
        RAISE EXCEPTION 'TEST 5 FALLÓ: RLS WITH CHECK debió haber rechazado la inserción cruzada!';
    EXCEPTION WHEN insufficient_privilege OR check_violation THEN
        RAISE NOTICE 'TEST 5 SUPERADO: Inserción cruzada rechazada correctamente por la política RLS.';
    END;
END $$;
ROLLBACK;

RESET ROLE;

\echo ''
\echo '>>> TEST 6: Lectura de membresías y organizaciones por usuario autenticado (app.usuario_sub)'
SET ROLE rah_app;
BEGIN;
-- Sin app.usuario_sub ni app.organizacion_id -> 0 filas
SELECT count(*) AS membresias_anonimo FROM membresias;
DO $$
DECLARE cnt INT;
BEGIN
    SELECT count(*) INTO cnt FROM membresias;
    IF cnt <> 0 THEN
        RAISE EXCEPTION 'TEST 6 FALLÓ: Se esperaban 0 membresías para anónimo, se obtuvieron %', cnt;
    END IF;
END $$;

-- Usuario A (e0000000-0000-4000-8000-000000000001) -> 1 membresía (Caracas), 1 organización
SET LOCAL app.usuario_sub = 'e0000000-0000-4000-8000-000000000001';
DO $$
DECLARE
    cnt_m INT;
    cnt_o INT;
BEGIN
    SELECT count(*) INTO cnt_m FROM membresias;
    SELECT count(*) INTO cnt_o FROM organizaciones;
    IF cnt_m <> 1 OR cnt_o <> 1 THEN
        RAISE EXCEPTION 'TEST 6 FALLÓ: Usuario A debía ver 1 membresía y 1 org, obtuvo m=%, o=%', cnt_m, cnt_o;
    END IF;
    RAISE NOTICE 'TEST 6.A SUPERADO: Usuario A ve únicamente su membresía de Caracas y su org.';
END $$;

-- Usuario AB (e0000000-0000-4000-8000-000000000003) -> 2 membresías, 2 organizaciones
SET LOCAL app.usuario_sub = 'e0000000-0000-4000-8000-000000000003';
DO $$
DECLARE
    cnt_m INT;
    cnt_o INT;
BEGIN
    SELECT count(*) INTO cnt_m FROM membresias;
    SELECT count(*) INTO cnt_o FROM organizaciones;
    IF cnt_m <> 2 OR cnt_o <> 2 THEN
        RAISE EXCEPTION 'TEST 6 FALLÓ: Usuario AB debía ver 2 membresías y 2 orgs, obtuvo m=%, o=%', cnt_m, cnt_o;
    END IF;
    RAISE NOTICE 'TEST 6.B SUPERADO: Usuario AB ve sus 2 membresías y sus 2 orgs (Caracas y Valencia).';
END $$;
ROLLBACK;
RESET ROLE;

\echo ''
\echo '----------------------------------------------------------------------'
\echo '¡TODAS LAS PRUEBAS DE ROW LEVEL SECURITY (RLS) COMPLETADAS CON ÉXITO!'
\echo '----------------------------------------------------------------------'
