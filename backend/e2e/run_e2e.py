"""Prueba de extremo a extremo de la matriz Sprint 02 contra el stack Docker REAL.

Keycloak (tokens reales por password grant de los usuarios DEV), backend en contenedor,
PostgreSQL con migraciones 0001+0002 y MinIO. No imprime tokens ni contraseñas.

Uso (desde backend/):
    E2E_PASSWORD=... python e2e/run_e2e.py --salida e2e/EVIDENCIA.md
Variables: E2E_API (http://localhost:8000), E2E_KEYCLOAK (http://localhost:8080),
E2E_REALM (crm-rah-dev), E2E_CLIENT (crm-rah-app), E2E_PASSWORD (obligatoria),
E2E_ADMIN_DB_URL (postgresql://rah_dev:...@localhost:5432/rah_vzla, para revocación y RLS),
E2E_APP_DB_URL (postgresql://rah_app:...@localhost:5432/rah_vzla).
"""
import argparse
import base64
import json
import os
import sys
import time
from datetime import datetime, timezone
from io import BytesIO

import httpx
import psycopg
from PIL import Image

API = os.environ.get('E2E_API', 'http://localhost:8000')
KC = os.environ.get('E2E_KEYCLOAK', 'http://localhost:8080')
REALM = os.environ.get('E2E_REALM', 'crm-rah-dev')
CLIENT = os.environ.get('E2E_CLIENT', 'crm-rah-app')
PASSWORD = os.environ['E2E_PASSWORD']
ADMIN_DB = os.environ['E2E_ADMIN_DB_URL']
APP_DB = os.environ['E2E_APP_DB_URL']

CARACAS = '11111111-1111-4111-8111-111111111111'
VALENCIA = '22222222-2222-4222-8222-222222222222'
RUN = datetime.now(timezone.utc).strftime('%H%M%S')

resultados: list[tuple[str, str, bool, str]] = []  # (fila matriz, comprobación, ok, detalle)


def check(fila: str, nombre: str, ok: bool, detalle: str = '') -> None:
    resultados.append((fila, nombre, bool(ok), detalle))
    print(f"[{'OK ' if ok else 'FALLA'}] {fila} · {nombre} {detalle}")


def token(usuario: str) -> str:
    r = httpx.post(f'{KC}/realms/{REALM}/protocol/openid-connect/token', data={
        'grant_type': 'password', 'client_id': CLIENT, 'username': usuario, 'password': PASSWORD,
        'scope': 'openid'}, timeout=60)
    r.raise_for_status()
    return r.json()['access_token']


def claims(tok: str) -> dict:
    payload = tok.split('.')[1]
    return json.loads(base64.urlsafe_b64decode(payload + '=' * (-len(payload) % 4)))


def h(tok: str, **extra) -> dict:
    return {'Authorization': f'Bearer {tok}', **extra}


def url(org, *partes) -> str:
    return '/'.join([f'{API}/api/v2/organizaciones/{org}', *map(str, partes)]).rstrip('/')


def inmueble(ref: str, titulo: str) -> dict:
    return {'titulo': titulo, 'tipo': 'apartamento', 'operacion': 'venta', 'precio': '85000.00',
            'moneda': 'USD', 'zona': 'Zona ficticia', 'codigo_referencia': ref}


def png() -> bytes:
    buf = BytesIO()
    Image.new('RGB', (64, 48), (27, 108, 128)).save(buf, format='PNG')
    return buf.getvalue()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--salida', required=True)
    args = ap.parse_args()
    c = httpx.Client(timeout=60)

    # --- identidad real
    ta, tb, tab = token('usuario-a'), token('usuario-b'), token('usuario-ab')
    ca = claims(ta)
    aud = ca['aud'] if isinstance(ca['aud'], list) else [ca['aud']]
    check('Identidad', 'token real Keycloak: iss/aud/sub', 'crm-rah-api' in aud,
          f"iss={ca['iss']} aud={aud} sub={ca['sub']}")
    me = c.get(f'{API}/api/v2/me', headers=h(ta))
    check('Identidad', 'GET /me usuario-a → solo Caracas', me.status_code == 200 and
          [o['id'] for o in me.json()['organizaciones']] == [CARACAS], f'status={me.status_code}')

    # --- 1. REF repetida entre organizaciones
    ref = f'E2E-{RUN}'
    ra = c.post(url(CARACAS, 'inmuebles'), json=inmueble(ref, 'E2E DEMO Caracas ficticio'), headers=h(ta))
    rb = c.post(url(VALENCIA, 'inmuebles'), json=inmueble(ref, 'E2E DEMO Valencia ficticio'), headers=h(tb))
    ok = ra.status_code == rb.status_code == 201 and ra.json()['id'] != rb.json()['id']
    check('A y B crean misma referencia', f'{ref} en ambas, IDs distintos', ok, f'{ra.status_code}/{rb.status_code}')
    ia, ib = ra.json()['id'], rb.json()['id']
    check('A y B crean misma referencia', 'precio string decimal', ra.json()['precio'] == '85000.00')
    dup = c.post(url(CARACAS, 'inmuebles'), json=inmueble(ref, 'Duplicado'), headers=h(ta))
    check('A y B crean misma referencia', 'duplicado en la misma org → 409', dup.status_code == 409, str(dup.status_code))

    # --- 2. A consulta listado/UUID de B
    r = c.get(url(VALENCIA, 'inmuebles'), headers=h(ta))
    check('A consulta recursos de B', 'listado de Valencia → 403', r.status_code == 403 and 'Valencia ficticio' not in r.text,
          str(r.status_code))
    r = c.get(url(CARACAS, 'inmuebles', ib), headers=h(ta))
    check('A consulta recursos de B', 'UUID de B bajo su org → 404', r.status_code == 404, str(r.status_code))
    r = c.get(url(VALENCIA, 'inmuebles', ib), headers=h(ta))
    check('A consulta recursos de B', 'UUID de B bajo org B → 403', r.status_code == 403, str(r.status_code))
    lista = c.get(url(CARACAS, 'inmuebles'), headers=h(ta)).json()
    check('A consulta recursos de B', 'listado propio sin filas de B',
          {i['organizacion_id'] for i in lista} == {CARACAS} and ib not in {i['id'] for i in lista}, f'{len(lista)} filas')

    # --- 3. org manipulada en JSON, URL o cabecera
    r = c.post(url(CARACAS, 'inmuebles'), json=inmueble(f'{ref}-J', 'x') | {'organizacion_id': VALENCIA}, headers=h(ta))
    check('A manipula organizacion_id', 'JSON con organizacion_id → 422', r.status_code == 422, str(r.status_code))
    r = c.post(url(CARACAS, 'inmuebles'), json=inmueble(f'{ref}-H', 'E2E cabecera'),
               headers=h(ta, **{'X-Organization-ID': VALENCIA}))
    check('A manipula organizacion_id', 'cabecera X-Organization-ID ignorada (queda en Caracas)',
          r.status_code == 201 and r.json()['organizacion_id'] == CARACAS, str(r.status_code))
    r = c.post(url(VALENCIA, 'inmuebles'), json=inmueble(f'{ref}-U', 'x'), headers=h(ta))
    check('A manipula organizacion_id', 'URL con org B → 403', r.status_code == 403, str(r.status_code))
    with psycopg.connect(ADMIN_DB) as db:
        n = db.execute('SELECT count(*) FROM inmuebles WHERE codigo_referencia LIKE %s AND organizacion_id = %s',
                       (f'{ref}-%', VALENCIA)).fetchone()[0]
    check('A manipula organizacion_id', 'ningún registro creado en Valencia', n == 0, f'{n} filas')

    # --- 4. foto real, URL firmada y B intentando obtenerla
    up = c.post(url(CARACAS, 'inmuebles', ia, 'media'), headers=h(tab),
                files={'archivo': ('salon.png', png(), 'image/png')}, data={'etiqueta_estancia': 'salon'})
    check('Fotos privadas', 'gerente (usuario-ab) sube foto a Caracas → 201', up.status_code == 201, str(up.status_code))
    media = c.get(url(CARACAS, 'inmuebles', ia, 'media'), headers=h(ta)).json()
    firmada = media[0]['url_temporal'] if media else ''
    check('Fotos privadas', 'clave con prefijo organizaciones/{org}/inmuebles/{id}/',
          f'/organizaciones/{CARACAS}/inmuebles/{ia}/originales/' in firmada)
    descarga = httpx.get(firmada, timeout=60)
    check('Fotos privadas', 'URL firmada abre desde el host (MinIO real)',
          descarga.status_code == 200 and descarga.content == png(), f'status={descarga.status_code}')
    sin_firma = httpx.get(firmada.split('?')[0], timeout=60)
    check('Fotos privadas', 'mismo objeto sin firma → denegado por MinIO', sin_firma.status_code == 403,
          f'status={sin_firma.status_code}')
    r1 = c.get(url(CARACAS, 'inmuebles', ia, 'media'), headers=h(tb))
    r2 = c.get(url(VALENCIA, 'inmuebles', ia, 'media'), headers=h(tb))
    check('B pide URL temporal de A', 'org A en URL → 403 sin URL', r1.status_code == 403 and 'X-Amz' not in r1.text,
          str(r1.status_code))
    check('B pide URL temporal de A', 'org B en URL → 404 sin URL', r2.status_code == 404 and 'X-Amz' not in r2.text,
          str(r2.status_code))

    # --- 5. sin sesión
    for metodo, ruta, kw in [('get', url(CARACAS, 'inmuebles', ia, 'media'), {}),
                             ('post', url(CARACAS, 'inmuebles', ia, 'media'),
                              {'files': {'archivo': ('a.png', png(), 'image/png')}}),
                             ('get', f'{API}/api/v2/me', {})]:
        r = getattr(c, metodo)(ruta, **kw)
        check('Sin sesión', f'{metodo.upper()} {ruta.replace(API, "")} → 401', r.status_code == 401, str(r.status_code))
    r = c.get(f'{API}/api/v2/me', headers={'Authorization': 'Bearer ' + ta[:-6] + 'AAAAAA'})
    check('Sin sesión', 'token con firma alterada → 401', r.status_code == 401, str(r.status_code))

    # --- 6. rol insuficiente (no hay usuario marketing en el realm DEV: se usa asesor)
    with psycopg.connect(ADMIN_DB) as db:
        m_b = db.execute("SELECT m.id FROM membresias m JOIN usuarios u ON u.id = m.usuario_id "
                         "WHERE u.subject = %s AND m.organizacion_id = %s", (claims(tab)['sub'], CARACAS)).fetchone()[0]
    r = c.delete(url(CARACAS, 'membresias', m_b), headers=h(ta))
    check('Rol insuficiente', 'asesor intenta borrar la membresía de otro → 403', r.status_code == 403, str(r.status_code))
    r = c.patch(url(CARACAS, 'inmuebles', ia), json={'titulo': 'Cambio no permitido'}, headers=h(ta))
    check('Rol insuficiente', 'asesor intenta editar → 403', r.status_code == 403, str(r.status_code))

    # --- 7. usuario dual
    la = c.get(url(CARACAS, 'inmuebles'), headers=h(tab)).json()
    lb = c.get(url(VALENCIA, 'inmuebles'), headers=h(tab)).json()
    check('Usuario dual', 'selección Caracas → solo Caracas', {i['organizacion_id'] for i in la} == {CARACAS},
          f'{len(la)} filas')
    check('Usuario dual', 'selección Valencia → solo Valencia', {i['organizacion_id'] for i in lb} == {VALENCIA},
          f'{len(lb)} filas')
    r = c.get(url(CARACAS, 'inmuebles', ib), headers=h(tab))
    check('Usuario dual', 'inmueble de Valencia bajo selección Caracas → 404', r.status_code == 404, str(r.status_code))

    # --- 8. API v1
    for ruta in ('/api/v1/inmuebles', f'/api/v1/inmuebles/{ia}', f'/api/v1/inmuebles/{ia}/media'):
        r = c.get(API + ruta)
        check('API v1 deshabilitada', f'GET {ruta} → 404', r.status_code == 404 and 'DEMO' not in r.text, str(r.status_code))

    # --- 9. revocación con sesión abierta (simulada en BD: no hay propietario en el realm DEV)
    sub_ab = claims(tab)['sub']
    with psycopg.connect(ADMIN_DB) as db:
        db.execute("UPDATE membresias SET estatus = 'inactiva' WHERE organizacion_id = %s AND usuario_id = "
                   "(SELECT id FROM usuarios WHERE subject = %s)", (CARACAS, sub_ab))
    try:
        r1 = c.get(url(CARACAS, 'inmuebles'), headers=h(tab))
        r2 = c.get(url(VALENCIA, 'inmuebles'), headers=h(tab))
        check('Revocación con sesión abierta', 'mismo token, membresía Caracas inactiva → 403', r1.status_code == 403,
              str(r1.status_code))
        check('Revocación con sesión abierta', 'membresía Valencia intacta → 200', r2.status_code == 200, str(r2.status_code))
    finally:
        with psycopg.connect(ADMIN_DB) as db:
            db.execute("UPDATE membresias SET estatus = 'activa' WHERE organizacion_id = %s AND usuario_id = "
                       "(SELECT id FROM usuarios WHERE subject = %s)", (CARACAS, sub_ab))

    # --- 10. RLS / pool: tras A y B, conexión del rol de app sin contexto no ve filas
    for _ in range(3):
        c.get(url(CARACAS, 'inmuebles'), headers=h(ta))
        c.get(url(VALENCIA, 'inmuebles'), headers=h(tb))
    with psycopg.connect(APP_DB) as db:
        sup, byp = db.execute('SELECT rolsuper, rolbypassrls FROM pg_roles WHERE rolname = current_user').fetchone()
        n0 = db.execute('SELECT count(*) FROM inmuebles').fetchone()[0]
        db.execute("SELECT set_config('app.organizacion_id', %s, true)", (CARACAS,))
        orgs = {r[0] for r in db.execute('SELECT DISTINCT organizacion_id::text FROM inmuebles').fetchall()}
    check('RLS / pool', 'rah_app sin SUPERUSER ni BYPASSRLS', (sup, byp) == (False, False))
    check('RLS / pool', 'consulta sin contexto → 0 filas', n0 == 0, f'{n0} filas')
    check('RLS / pool', 'consulta sin filtro con contexto Caracas → solo Caracas', orgs == {CARACAS}, str(orgs))

    escribir(args.salida, ca)
    return 0 if all(ok for _, _, ok, _ in resultados) else 1


def escribir(path: str, ca: dict) -> None:
    ok = sum(1 for r in resultados if r[2])
    lineas = [
        '# Evidencia E2E Sprint 02 · API v2 contra stack Docker real',
        '',
        f"- Fecha (UTC): {datetime.now(timezone.utc).isoformat(timespec='seconds')}",
        f'- API: `{API}` · Keycloak: `{KC}` realm `{REALM}` cliente `{CLIENT}`',
        f"- Token real de usuario-a: iss `{ca['iss']}`, aud `{ca['aud']}`, sub `{ca['sub']}` (sin imprimir el token)",
        f'- Resultado: **{ok}/{len(resultados)} comprobaciones OK**',
        '',
        '| Fila de la matriz | Comprobación | Resultado | Detalle |',
        '| --- | --- | --- | --- |',
    ]
    lineas += [f"| {f} | {n} | {'OK' if o else '**FALLA**'} | {d} |" for f, n, o, d in resultados]
    lineas += [
        '',
        '## Limitaciones de esta corrida',
        '',
        '- El realm DEV no tiene usuarios `marketing` ni `propietario`: el 403 por rol se probó con `asesor`;'
        ' el caso exacto `marketing` y el DELETE de membresías por propietario están cubiertos por los tests'
        ' de integración (`tests/test_v2_aislamiento.py`).',
        '- La revocación se simuló marcando la membresía `inactiva` en BD (y se restauró), con el token ya emitido.',
        '- Datos 100 % ficticios.',
    ]
    with open(path, 'w') as f:
        f.write('\n'.join(lineas) + '\n')


if __name__ == '__main__':
    sys.exit(main())
