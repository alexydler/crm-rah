"""Matriz de aceptación de docs/SPRINT_02_MULTIAGENCIA.md contra PostgreSQL real con RLS."""
from io import BytesIO
from urllib.parse import urlparse

import pytest
from PIL import Image
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError, IntegrityError

from tests.datos import (
    ORG_A, ORG_B, ORG_SUSP, SUB_A, SUB_AB, SUB_B, SUB_CONS, SUB_DESCONOCIDO, SUB_MKT, SUB_NADIE, SUB_SUSP,
)

BASE = {
    'titulo': 'DEMO - apartamento ficticio', 'tipo': 'apartamento', 'operacion': 'venta',
    'precio': '85000.00', 'moneda': 'USD', 'zona': 'Zona ficticia', 'estado_ve': 'Carabobo',
    'municipio': 'Valencia', 'urbanizacion': 'Sector ficticio',
}


def url(org, *partes) -> str:
    return '/'.join([f'/api/v2/organizaciones/{org}', *map(str, partes)]).rstrip('/')


def png() -> bytes:
    buf = BytesIO()
    Image.new('RGB', (4, 4), (27, 108, 128)).save(buf, format='PNG')
    return buf.getvalue()


def crear(client, h, org, **campos):
    r = client.post(url(org, 'inmuebles'), json=BASE | campos, headers=h)
    assert r.status_code == 201, r.text
    return r.json()


def subir_foto(client, h, org, inmueble_id):
    return client.post(url(org, 'inmuebles', inmueble_id, 'media'), headers=h,
                       files={'archivo': ('salon.png', png(), 'image/png')}, data={'etiqueta_estancia': 'salon'})


@pytest.fixture
def datos(client, auth_header):
    """A y B con un inmueble y una foto cada uno."""
    ha, hb = auth_header(SUB_A), auth_header(SUB_B)
    ia = crear(client, ha, ORG_A, codigo_referencia='REF-001', titulo='DEMO A ficticio')
    ib = crear(client, hb, ORG_B, codigo_referencia='REF-001', titulo='DEMO B ficticio')
    fa = subir_foto(client, ha, ORG_A, ia['id'])
    fb = subir_foto(client, hb, ORG_B, ib['id'])
    assert fa.status_code == fb.status_code == 201, (fa.text, fb.text)
    return {'ha': ha, 'hb': hb, 'ia': ia, 'ib': ib, 'fa': fa.json(), 'fb': fb.json()}


# ------------------------------------------------- A y B crean REF-001: ambos válidos, IDs distintos

def test_referencia_repetida_entre_organizaciones(client, datos):
    ia, ib = datos['ia'], datos['ib']
    assert ia['codigo_referencia'] == ib['codigo_referencia'] == 'REF-001'
    assert ia['id'] != ib['id']
    assert ia['organizacion_id'] == str(ORG_A) and ib['organizacion_id'] == str(ORG_B)
    # Dentro de la misma organización sí es conflicto.
    r = client.post(url(ORG_A, 'inmuebles'), json=BASE | {'codigo_referencia': 'REF-001'}, headers=datos['ha'])
    assert r.status_code == 409


def test_patch_propietario(client, datos):
    ia = datos['ia']['id']
    r = client.patch(url(ORG_A, 'inmuebles', ia), json={'precio': '90000.50', 'estado': 'disponible'},
                     headers=datos['ha'])
    assert r.status_code == 200, r.text
    assert r.json()['precio'] == '90000.50' and r.json()['estado'] == 'disponible'
    r = client.patch(url(ORG_A, 'inmuebles', ia), json={'titulo': None}, headers=datos['ha'])
    assert r.status_code == 422


def test_precio_string_decimal(client, datos):
    assert datos['ia']['precio'] == '85000.00'
    r = client.get(url(ORG_A, 'inmuebles', datos['ia']['id']), headers=datos['ha'])
    assert r.json()['precio'] == '85000.00' and isinstance(r.json()['precio'], str)


# ------------------------------------------------- A consulta listado/UUID de B → 403/404 sin filtrar ficha

def test_a_no_ve_listado_de_b(client, datos):
    r = client.get(url(ORG_A, 'inmuebles'), headers=datos['ha'])
    assert [i['id'] for i in r.json()] == [datos['ia']['id']]
    r = client.get(url(ORG_B, 'inmuebles'), headers=datos['ha'])
    assert r.status_code == 403
    assert 'DEMO B' not in r.text


@pytest.mark.parametrize('metodo,sufijo', [('get', ''), ('get', 'media'), ('patch', '')])
def test_a_no_accede_a_inmueble_de_b_por_uuid(client, datos, metodo, sufijo):
    ib = datos['ib']['id']
    kw = {'json': {'titulo': 'Intento de A'}} if metodo == 'patch' else {}
    # Con la org propia en la URL y UUID ajeno: 404, como si no existiera.
    r = getattr(client, metodo)(url(ORG_A, 'inmuebles', ib, sufijo), headers=datos['ha'], **kw)
    assert r.status_code == 404
    assert 'DEMO B' not in r.text and str(ORG_B) not in r.text
    # Con la org ajena en la URL: 403 por falta de membresía.
    r = getattr(client, metodo)(url(ORG_B, 'inmuebles', ib, sufijo), headers=datos['ha'], **kw)
    assert r.status_code == 403
    assert 'DEMO B' not in r.text


def test_a_no_sube_foto_a_inmueble_de_b(client, datos, storage):
    antes = set(storage.objetos)
    r = subir_foto(client, datos['ha'], ORG_A, datos['ib']['id'])
    assert r.status_code == 404
    assert set(storage.objetos) == antes


# ------------------------------------------------- A manipula organizacion_id en JSON, URL o cabeceras

def _conteo(admin_engine, org) -> int:
    with admin_engine.connect() as c:
        return c.scalar(text('SELECT count(*) FROM inmuebles WHERE organizacion_id = :o'), {'o': org})


def test_organizacion_en_json_rechazada(client, datos, admin_engine):
    antes = _conteo(admin_engine, ORG_B)
    for campo in ({'organizacion_id': str(ORG_B)}, {'id': datos['ib']['id']}, {'creado_por': SUB_B}):
        r = client.post(url(ORG_A, 'inmuebles'), json=BASE | campo, headers=datos['ha'])
        assert r.status_code == 422, campo
    r = client.patch(url(ORG_A, 'inmuebles', datos['ia']['id']), json={'organizacion_id': str(ORG_B)},
                     headers=datos['ha'])
    assert r.status_code == 422
    assert _conteo(admin_engine, ORG_B) == antes


def test_cabecera_de_organizacion_ignorada(client, datos, admin_engine):
    h = datos['ha'] | {'X-Organization-ID': str(ORG_B), 'X-Organizacion-Id': str(ORG_B)}
    antes_b = _conteo(admin_engine, ORG_B)
    r = client.post(url(ORG_A, 'inmuebles'), json=BASE | {'codigo_referencia': 'HDR-1'}, headers=h)
    assert r.status_code == 201 and r.json()['organizacion_id'] == str(ORG_A)
    r = client.get(url(ORG_A, 'inmuebles'), headers=h)
    assert {i['organizacion_id'] for i in r.json()} == {str(ORG_A)}
    assert client.get(url(ORG_B, 'inmuebles'), headers=h).status_code == 403
    assert _conteo(admin_engine, ORG_B) == antes_b


def test_org_en_url_no_autoriza_crear(client, datos, admin_engine):
    antes = _conteo(admin_engine, ORG_B)
    r = client.post(url(ORG_B, 'inmuebles'), json=BASE | {'codigo_referencia': 'X'}, headers=datos['ha'])
    assert r.status_code == 403
    assert _conteo(admin_engine, ORG_B) == antes


def test_org_inexistente_misma_respuesta(client, datos):
    r = client.get(url('99999999-9999-4999-8999-999999999999', 'inmuebles'), headers=datos['ha'])
    assert r.status_code == 403


# ------------------------------------------------- B solicita URL temporal de imagen de A → no se emite

def test_b_no_obtiene_url_firmada_de_a(client, datos, storage):
    ia = datos['ia']['id']
    clave_a = next(k for k in storage.objetos if k.startswith(f'org/{ORG_A}/'))
    storage.firmadas.clear()
    assert client.get(url(ORG_A, 'inmuebles', ia, 'media'), headers=datos['hb']).status_code == 403
    assert client.get(url(ORG_B, 'inmuebles', ia, 'media'), headers=datos['hb']).status_code == 404
    assert clave_a not in storage.firmadas and storage.firmadas == []


def test_claves_minio_con_prefijo_de_org(client, datos, storage):
    ia, ib = datos['ia']['id'], datos['ib']['id']
    claves = list(storage.objetos)
    assert any(k.startswith(f'org/{ORG_A}/inmuebles/{ia}/originales/') for k in claves)
    assert any(k.startswith(f'org/{ORG_B}/inmuebles/{ib}/originales/') for k in claves)
    r = client.get(url(ORG_A, 'inmuebles', ia, 'media'), headers=datos['ha'])
    assert r.status_code == 200 and len(r.json()) == 1
    path = urlparse(r.json()[0]['url_temporal']).path
    assert f'/org/{ORG_A}/inmuebles/{ia}/' in path
    assert 'X-Amz-Expires=900' in r.json()[0]['url_temporal']


def test_presign_rechaza_clave_de_otra_org(storage):
    from app.storage import ClaveFueraDeOrganizacion
    with pytest.raises(ClaveFueraDeOrganizacion):
        storage.presign_get(ORG_B, f'org/{ORG_A}/inmuebles/x/originales/y.png')


def test_upload_valida_contenido(client, datos):
    r = client.post(url(ORG_A, 'inmuebles', datos['ia']['id'], 'media'), headers=datos['ha'],
                    files={'archivo': ('x.png', b'no soy una imagen', 'image/png')})
    assert r.status_code == 422


# ------------------------------------------------- Sin sesión: 401

@pytest.mark.parametrize('metodo,ruta', [
    ('get', '/api/v2/me'), ('get', '/api/v2/organizaciones'), ('get', '/api/v2/me/organizaciones'),
    ('get', url(ORG_A)), ('get', url(ORG_A, 'inmuebles')), ('post', url(ORG_A, 'inmuebles')),
    ('get', url(ORG_A, 'inmuebles', '11111111-0000-4000-8000-000000000000')),
    ('get', url(ORG_A, 'inmuebles', '11111111-0000-4000-8000-000000000000', 'media')),
    ('post', url(ORG_A, 'inmuebles', '11111111-0000-4000-8000-000000000000', 'media')),
])
def test_sin_sesion_401(client, metodo, ruta):
    r = getattr(client, metodo)(ruta)
    assert r.status_code == 401
    assert r.headers.get('www-authenticate') == 'Bearer'


def test_sin_sesion_no_lee_ni_sube_fotos(client, datos, storage):
    ia = datos['ia']['id']
    n = len(storage.objetos)
    storage.firmadas.clear()
    assert client.get(url(ORG_A, 'inmuebles', ia, 'media')).status_code == 401
    r = client.post(url(ORG_A, 'inmuebles', ia, 'media'), files={'archivo': ('a.png', png(), 'image/png')})
    assert r.status_code == 401
    assert len(storage.objetos) == n and storage.firmadas == []


@pytest.mark.parametrize('kw', [{'exp_delta': -3600}, {'aud': 'otra-app'}, {'iss': 'http://evil/realms/x'}])
def test_token_invalido_401(client, auth_header, kw):
    assert client.get(url(ORG_A, 'inmuebles'), headers=auth_header(SUB_A, **kw)).status_code == 401


def test_esquema_basic_no_es_bearer(client):
    assert client.get('/api/v2/me', headers={'Authorization': 'Basic dXNlcjpwYXNz'}).status_code == 401


# ------------------------------------------------- Rol insuficiente: 403

def test_marketing_no_revoca_miembros(client, datos, auth_header, admin_engine):
    with admin_engine.connect() as c:
        m_cons = c.scalar(text('SELECT m.id FROM membresias m JOIN usuarios u ON u.id = m.usuario_id WHERE u.subject = :s'), {'s': SUB_CONS})
    r = client.delete(url(ORG_A, 'membresias', m_cons), headers=auth_header(SUB_MKT))
    assert r.status_code == 403
    with admin_engine.connect() as c:
        assert c.scalar(text('SELECT estatus FROM membresias WHERE id = :i'), {'i': m_cons}) == 'activa'
    # Propietario sí puede; queda `inactiva` (no se borra la fila).
    assert client.delete(url(ORG_A, 'membresias', m_cons), headers=datos['ha']).status_code == 204
    with admin_engine.connect() as c:
        assert c.scalar(text('SELECT estatus FROM membresias WHERE id = :i'), {'i': m_cons}) == 'inactiva'


@pytest.mark.parametrize('sub', [SUB_MKT, SUB_CONS])
def test_roles_lectura_no_escriben(client, datos, auth_header, sub):
    h = auth_header(sub)
    ia = datos['ia']['id']
    assert client.get(url(ORG_A, 'inmuebles'), headers=h).status_code == 200
    assert client.post(url(ORG_A, 'inmuebles'), json=BASE, headers=h).status_code == 403
    assert client.patch(url(ORG_A, 'inmuebles', ia), json={'titulo': 'Cambio'}, headers=h).status_code == 403
    assert subir_foto(client, h, ORG_A, ia).status_code == 403


@pytest.mark.parametrize('sub', [SUB_NADIE, SUB_DESCONOCIDO])
def test_sin_membresia_403(client, auth_header, sub):
    assert client.get(url(ORG_A, 'inmuebles'), headers=auth_header(sub)).status_code == 403
    r = client.get('/api/v2/me', headers=auth_header(sub))
    assert r.status_code == 200 and r.json()['organizaciones'] == []


def test_claims_de_org_o_rol_en_token_ignorados(client, datos, auth_header):
    # El realm DEV emite mappers `organizaciones`/`rol`: el backend NO los usa para autorizar.
    h = auth_header(SUB_A, extra={'organizaciones': [str(ORG_B)], 'rol': 'propietario',
                                  'organizacion_id': str(ORG_B)})
    assert client.get(url(ORG_B, 'inmuebles'), headers=h).status_code == 403
    h = auth_header(SUB_CONS, extra={'rol': 'propietario'})
    assert client.post(url(ORG_A, 'inmuebles'), json=BASE, headers=h).status_code == 403


def test_usuario_desactivado_403(client, datos, admin_engine):
    with admin_engine.begin() as c:
        c.execute(text("UPDATE usuarios SET estado = 'bloqueado' WHERE subject = :s"), {'s': SUB_A})
    assert client.get(url(ORG_A, 'inmuebles'), headers=datos['ha']).status_code == 403


def test_organizacion_suspendida_403(client, auth_header):
    h = auth_header(SUB_SUSP)
    assert client.get(url(ORG_SUSP, 'inmuebles'), headers=h).status_code == 403
    assert client.get('/api/v2/organizaciones', headers=h).json() == []


# ------------------------------------------------- Usuario con dos membresías ve solo la org seleccionada

def test_usuario_dual_ve_solo_org_seleccionada(client, datos, auth_header):
    h = auth_header(SUB_AB)
    me = client.get('/api/v2/me', headers=h).json()
    assert me['sub'] == SUB_AB
    assert {o['id'] for o in me['organizaciones']} == {str(ORG_A), str(ORG_B)}
    assert all(o['rol'] == 'gerente' for o in me['organizaciones'])
    for ruta in ('/api/v2/organizaciones', '/api/v2/me/organizaciones'):
        assert {o['id'] for o in client.get(ruta, headers=h).json()} == {str(ORG_A), str(ORG_B)}

    la = client.get(url(ORG_A, 'inmuebles'), headers=h).json()
    lb = client.get(url(ORG_B, 'inmuebles'), headers=h).json()
    assert [i['id'] for i in la] == [datos['ia']['id']]
    assert [i['id'] for i in lb] == [datos['ib']['id']]
    # Recurso de B pedido bajo la selección A → 404 aunque también sea miembro de B.
    assert client.get(url(ORG_A, 'inmuebles', datos['ib']['id']), headers=h).status_code == 404
    assert client.get(url(ORG_A, 'inmuebles', datos['ib']['id'], 'media'), headers=h).status_code == 404
    # Crea en B: queda en B, no en A.
    nuevo = crear(client, h, ORG_B, codigo_referencia='DUAL-1')
    assert nuevo['organizacion_id'] == str(ORG_B)
    assert nuevo['id'] not in {i['id'] for i in client.get(url(ORG_A, 'inmuebles'), headers=h).json()}


def test_me_no_expone_terceros(client, datos, auth_header):
    me = client.get('/api/v2/me', headers=auth_header(SUB_A)).json()
    assert [o['id'] for o in me['organizaciones']] == [str(ORG_A)]
    assert SUB_B not in str(me) and SUB_AB not in str(me)


# ------------------------------------------------- API v1 deshabilitada por defecto

@pytest.mark.parametrize('metodo,ruta', [
    ('get', '/api/v1/inmuebles'), ('post', '/api/v1/inmuebles'),
    ('get', '/api/v1/inmuebles/11111111-0000-4000-8000-000000000000'),
    ('get', '/api/v1/inmuebles/11111111-0000-4000-8000-000000000000/media'),
])
def test_v1_deshabilitada(client, datos, metodo, ruta):
    r = getattr(client, metodo)(ruta)
    assert r.status_code == 404
    assert 'DEMO A' not in r.text and 'DEMO B' not in r.text


def test_v1_demo_habilitada_solo_ve_org_demo(client_v1_demo, auth_header):
    c = client_v1_demo
    crear(c, auth_header(SUB_A), ORG_A, codigo_referencia='PRIV-A')
    r = c.post('/api/v1/inmuebles', json=BASE | {'codigo_referencia': 'DEMO-V1'})
    assert r.status_code == 201
    listado = c.get('/api/v1/inmuebles').json()
    assert [i['codigo_referencia'] for i in listado] == ['DEMO-V1']


# ------------------------------------------------- Revocación con sesión abierta

def test_revocacion_aplica_en_siguiente_request(client, datos, auth_header, admin_engine):
    h_ab = auth_header(SUB_AB)  # el mismo token sigue siendo criptográficamente válido
    assert client.get(url(ORG_A, 'inmuebles'), headers=h_ab).status_code == 200
    with admin_engine.connect() as c:
        m = c.scalar(text('SELECT m.id FROM membresias m JOIN usuarios u ON u.id = m.usuario_id WHERE u.subject = :s AND m.organizacion_id = :o'),
                     {'s': SUB_AB, 'o': ORG_A})
    assert client.delete(url(ORG_A, 'membresias', m), headers=datos['ha']).status_code == 204
    assert client.get(url(ORG_A, 'inmuebles'), headers=h_ab).status_code == 403
    assert client.get(url(ORG_A, 'inmuebles', datos['ia']['id'], 'media'), headers=h_ab).status_code == 403
    # Su membresía en B no se ve afectada.
    assert client.get(url(ORG_B, 'inmuebles'), headers=h_ab).status_code == 200
    assert {o['id'] for o in client.get('/api/v2/me', headers=h_ab).json()['organizaciones']} == {str(ORG_B)}


def test_propietario_no_revoca_membresia_de_otra_org(client, datos, admin_engine):
    with admin_engine.connect() as c:
        m_b = c.scalar(text('SELECT m.id FROM membresias m JOIN usuarios u ON u.id = m.usuario_id WHERE u.subject = :s'), {'s': SUB_B})
    assert client.delete(url(ORG_A, 'membresias', m_b), headers=datos['ha']).status_code == 404


# ------------------------------------------------- RLS y pool reutilizado

def test_pool_reutilizado_sin_filas_cruzadas(client, datos, app_engine):
    assert app_engine.pool.size() == 1
    for _ in range(3):
        la = client.get(url(ORG_A, 'inmuebles'), headers=datos['ha']).json()
        lb = client.get(url(ORG_B, 'inmuebles'), headers=datos['hb']).json()
        assert {i['organizacion_id'] for i in la} == {str(ORG_A)}
        assert {i['organizacion_id'] for i in lb} == {str(ORG_B)}
    # La conexión devuelta al pool no conserva el tenant del último request.
    with app_engine.connect() as conn:
        assert conn.scalar(text("SELECT current_setting('app.organizacion_id', true)")) in (None, '')
        assert conn.scalar(text('SELECT count(*) FROM inmuebles')) == 0
        assert conn.scalar(text('SELECT count(*) FROM inmueble_media')) == 0


def test_rls_consultas_sin_filtro_deliberadas(datos, app_engine):
    with app_engine.begin() as conn:
        conn.execute(text("SELECT set_config('app.organizacion_id', :o, true)"), {'o': str(ORG_A)})
        orgs = conn.scalars(text('SELECT DISTINCT organizacion_id FROM inmuebles')).all()
        assert orgs == [ORG_A]
        assert conn.scalars(text('SELECT DISTINCT organizacion_id FROM inmueble_media')).all() == [ORG_A]
        # UPDATE/DELETE sin filtro no tocan B.
        conn.execute(text("UPDATE inmuebles SET titulo = 'tocado'"))
    with app_engine.begin() as conn:
        conn.execute(text("SELECT set_config('app.organizacion_id', :o, true)"), {'o': str(ORG_B)})
        assert conn.scalar(text("SELECT count(*) FROM inmuebles WHERE titulo = 'tocado'")) == 0


def test_rls_with_check_impide_insertar_en_otra_org(datos, app_engine):
    with pytest.raises(DBAPIError) as exc, app_engine.begin() as conn:
        conn.execute(text("SELECT set_config('app.organizacion_id', :o, true)"), {'o': str(ORG_A)})
        conn.execute(text(
            "INSERT INTO inmuebles (organizacion_id, titulo, tipo, operacion, precio, moneda, zona, extras, "
            "descripcion, estado) VALUES (:b, 'x', 'casa', 'venta', 1, 'USD', 'z', '{}', '', 'borrador')"
        ), {'b': ORG_B})
    assert 'row-level security' in str(exc.value)


def test_rol_app_sin_privilegios(app_engine):
    with app_engine.connect() as conn:
        row = conn.execute(text(
            'SELECT rolsuper, rolbypassrls FROM pg_roles WHERE rolname = current_user')).one()
        assert row == (False, False)
        dueno = conn.scalar(text("SELECT tableowner = current_user FROM pg_tables WHERE tablename = 'inmuebles'"))
        assert dueno is False


def test_fk_compuesta_impide_media_cruzada(datos, admin_engine):
    with pytest.raises(IntegrityError), admin_engine.begin() as conn:
        conn.execute(text(
            "INSERT INTO inmueble_media (organizacion_id, inmueble_id, object_key, tipo, orden, content_type) "
            "VALUES (:a, :ib, 'org/x/cruzada.png', 'foto', 0, 'image/png')"
        ), {'a': ORG_A, 'ib': datos['ib']['id']})

