"""Infraestructura de pruebas de aislamiento multiorganización.

- PostgreSQL REAL: si existe ``TEST_PG_ADMIN_URL`` se usa esa instancia (debe ser desechable);
  si no, se crea un cluster temporal con ``initdb``/``pg_ctl`` (``PG_BIN`` o
  ``/Library/PostgreSQL/16/bin``, ``/usr/lib/postgresql/16/bin``). Sin PostgreSQL disponible,
  las pruebas de integración se OMITEN (skip) indicándolo; nunca se simulan con SQLite.
- Esquema: ``Base.metadata.create_all`` + políticas RLS de ``rls_test.sql``. Es un ESPEJO DE PRUEBA
  del diseño de ``db/design``; la migración real (Alembic) la entrega el DBA y debe pasar
  estas mismas pruebas apuntando ``TEST_PG_ADMIN_URL`` a una BD migrada.
- La app se conecta con un rol sin SUPERUSER ni BYPASSRLS y que no es dueño de las tablas.
- Tokens: RS256 firmados con una clave generada en la sesión; JWKS local, sin Keycloak.
- MinIO: almacenamiento falso en memoria; las URLs se firman con boto3 real (offline).
"""
import os
import shutil
import socket
import subprocess
import tempfile
import time
import uuid
from dataclasses import dataclass
from pathlib import Path

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from app import auth, db as app_db, storage as app_storage
from app.config import settings
from app.main import create_app
from app.models import Base

from tests.datos import (APP_ROLE, AUDIENCE, ISSUER, MEMBRESIAS, ORG_A, ORG_B, ORG_SUSP, ORG_V1_DEMO)

APP_PASSWORD = 'solo_tests_' + uuid.uuid4().hex[:12]


# ----------------------------------------------------------------------------- PostgreSQL

def _pg_bin() -> Path | None:
    candidatos = [os.environ.get('PG_BIN'), '/Library/PostgreSQL/16/bin', '/usr/lib/postgresql/16/bin',
                  '/opt/homebrew/opt/postgresql@16/bin', '/usr/local/opt/postgresql@16/bin']
    for c in candidatos:
        if c and (Path(c) / 'initdb').exists():
            return Path(c)
    found = shutil.which('initdb')
    return Path(found).parent if found else None


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]


@pytest.fixture(scope='session')
def pg_admin_url():
    if os.environ.get('TEST_PG_ADMIN_URL'):
        yield os.environ['TEST_PG_ADMIN_URL']
        return
    pg_bin = _pg_bin()
    if pg_bin is None:
        pytest.skip('PostgreSQL no disponible: define TEST_PG_ADMIN_URL o PG_BIN para pruebas de integración')
    tmp = Path(tempfile.mkdtemp(prefix='rahpg'))
    data = tmp / 'data'
    port = _free_port()
    subprocess.run([pg_bin / 'initdb', '-D', data, '-U', 'pgadmin', '-A', 'trust', '--no-sync', '-E', 'UTF8'],
                   check=True, capture_output=True)
    subprocess.run(
        [pg_bin / 'pg_ctl', '-D', data, '-l', tmp / 'pg.log', '-w', '-o',
         f"-p {port} -c listen_addresses=127.0.0.1 -c unix_socket_directories='{tmp}' -c fsync=off", 'start'],
        check=True, capture_output=True,
    )
    try:
        subprocess.run([pg_bin / 'createdb', '-h', '127.0.0.1', '-p', str(port), '-U', 'pgadmin', 'rah_test'],
                       check=True, capture_output=True)
        yield f'postgresql+psycopg://pgadmin@127.0.0.1:{port}/rah_test'
    finally:
        subprocess.run([pg_bin / 'pg_ctl', '-D', data, '-m', 'immediate', 'stop'], capture_output=True)
        shutil.rmtree(tmp, ignore_errors=True)


@pytest.fixture(scope='session')
def admin_engine(pg_admin_url):
    eng = create_engine(pg_admin_url)
    rls_sql = (Path(__file__).parent / 'rls_test.sql').read_text()
    with eng.begin() as conn:
        conn.execute(text('DROP SCHEMA IF EXISTS public CASCADE; CREATE SCHEMA public'))
        Base.metadata.create_all(conn)
        conn.execute(text(f"""
            DO $$ BEGIN
              IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '{APP_ROLE}') THEN
                EXECUTE 'DROP OWNED BY {APP_ROLE}'; EXECUTE 'DROP ROLE {APP_ROLE}';
              END IF;
            END $$;
            CREATE ROLE {APP_ROLE} LOGIN NOSUPERUSER NOBYPASSRLS NOCREATEDB NOCREATEROLE
              PASSWORD '{APP_PASSWORD}';
        """))
        conn.execute(text(rls_sql.replace(':app_role', APP_ROLE)))
    yield eng
    eng.dispose()


@pytest.fixture(scope='session')
def app_engine(admin_engine, pg_admin_url):
    url = make_url(pg_admin_url).set(username=APP_ROLE, password=APP_PASSWORD)
    # pool de UNA conexión: fuerza que requests consecutivos de A y B reutilicen la misma.
    eng = create_engine(url, pool_size=1, max_overflow=0, pool_pre_ping=True)
    yield eng
    eng.dispose()


@pytest.fixture(autouse=False)
def seed(admin_engine):
    with admin_engine.begin() as conn:
        conn.execute(text('TRUNCATE inmueble_media, inmuebles, membresias, organizaciones CASCADE'))
        conn.execute(text("""
            INSERT INTO organizaciones (id, slug, nombre, estatus) VALUES
              (:a, 'demo-caracas', 'Inmobiliaria DEMO A (Caracas)', 'activa'),
              (:b, 'demo-valencia', 'Inmobiliaria DEMO B (Valencia)', 'activa'),
              (:s, 'demo-suspendida', 'Inmobiliaria DEMO suspendida', 'suspendida'),
              (:v, 'demo-v1', 'Organización DEMO v1', 'activa')
        """), {'a': ORG_A, 'b': ORG_B, 's': ORG_SUSP, 'v': ORG_V1_DEMO})
        for org, sub, rol in MEMBRESIAS:
            conn.execute(text('INSERT INTO membresias (organizacion_id, usuario_sub, rol, estatus) '
                              "VALUES (:o, :s, :r, 'activa')"), {'o': org, 's': sub, 'r': rol})


# ----------------------------------------------------------------------------- tokens

@dataclass
class Firmante:
    private_key: object
    kid: str

    def token(self, sub: str, *, iss: str = ISSUER, aud: str = AUDIENCE, exp_delta: int = 300,
              extra: dict | None = None, kid: str | None = None, alg: str = 'RS256', key=None) -> str:
        now = int(time.time())
        claims = {'sub': sub, 'iss': iss, 'aud': aud, 'iat': now, 'exp': now + exp_delta,
                  'email': f'{sub}@ejemplo.invalid', 'name': f'Usuario ficticio {sub}'}
        claims.update(extra or {})
        return jwt.encode(claims, key or self.private_key, algorithm=alg, headers={'kid': kid or self.kid})


@pytest.fixture(scope='session')
def firmante() -> Firmante:
    return Firmante(rsa.generate_private_key(public_exponent=65537, key_size=2048), kid='test-kid-1')


@pytest.fixture(scope='session')
def verifier(firmante) -> auth.TokenVerifier:
    jwk = jwt.algorithms.RSAAlgorithm.to_jwk(firmante.private_key.public_key(), as_dict=True)
    jwks = jwt.PyJWKSet.from_dict({'keys': [jwk | {'kid': firmante.kid, 'use': 'sig', 'alg': 'RS256'}]})

    def resolver(token: str):
        kid = jwt.get_unverified_header(token).get('kid')
        for k in jwks.keys:
            if k.key_id == kid:
                return k.key
        raise jwt.InvalidTokenError('kid desconocido')

    return auth.TokenVerifier(ISSUER, AUDIENCE, resolver)


# ----------------------------------------------------------------------------- almacenamiento

class FakeStorage(app_storage.Storage):
    """put/delete en memoria; presign_get es el código REAL (chequeo de prefijo + firma boto3)."""

    def __init__(self):
        self.bucket = 'rah-vzla-media-test'
        self.expira = 900
        self._public = app_storage._s3_client('http://localhost:9000')
        self.objetos: dict[str, bytes] = {}
        self.firmadas: list[str] = []

    def put(self, key, body, content_type):
        self.objetos[key] = body

    def delete(self, key):
        self.objetos.pop(key, None)

    def presign_get(self, organizacion_id, key):
        url = super().presign_get(organizacion_id, key)
        self.firmadas.append(key)
        return url


@pytest.fixture
def storage() -> FakeStorage:
    return FakeStorage()


# ----------------------------------------------------------------------------- app

def _build_client(app_engine, verifier, storage) -> TestClient:
    SessionTest = sessionmaker(bind=app_engine, class_=app_db.TenantSession, expire_on_commit=False)

    def get_db_test():
        with SessionTest() as s:
            yield s

    app = create_app(settings)
    app.dependency_overrides[app_db.get_db] = get_db_test
    app.dependency_overrides[auth.get_token_verifier] = lambda: verifier
    app.dependency_overrides[app_storage.get_storage] = lambda: storage
    return TestClient(app)


@pytest.fixture
def client(seed, app_engine, verifier, storage) -> TestClient:
    assert settings.enable_v1_demo is False, 'Las pruebas asumen v1 deshabilitada por defecto'
    with _build_client(app_engine, verifier, storage) as c:
        yield c


@pytest.fixture
def client_v1_demo(seed, app_engine, verifier, storage, monkeypatch) -> TestClient:
    monkeypatch.setattr(settings, 'enable_v1_demo', True)
    monkeypatch.setattr(settings, 'v1_demo_organizacion_id', ORG_V1_DEMO)
    with _build_client(app_engine, verifier, storage) as c:
        yield c


@pytest.fixture
def auth_header(firmante):
    def _h(sub: str, **kw) -> dict[str, str]:
        return {'Authorization': f'Bearer {firmante.token(sub, **kw)}'}
    return _h
