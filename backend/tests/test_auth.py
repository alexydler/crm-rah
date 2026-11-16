"""Verificación de tokens OIDC (sin BD ni Keycloak)."""
import time

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from app.auth import TokenInvalido, TokenVerifier
from tests.datos import AUDIENCE, ISSUER


def test_token_valido(firmante, verifier):
    u = verifier.verify(firmante.token('sub-x'))
    assert u.sub == 'sub-x'


@pytest.mark.parametrize('kw', [
    {'iss': 'http://otro-issuer/realms/x'},
    {'aud': 'otra-audiencia'},
    {'exp_delta': -3600},
    {'kid': 'kid-desconocido'},
])
def test_token_rechazado(firmante, verifier, kw):
    with pytest.raises(TokenInvalido):
        verifier.verify(firmante.token('sub-x', **kw))


def test_firma_de_otra_clave(firmante, verifier):
    otra = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    with pytest.raises(TokenInvalido):
        verifier.verify(firmante.token('sub-x', key=otra))


def test_alg_none_y_hmac_rechazados(verifier):
    now = int(time.time())
    claims = {'sub': 'x', 'iss': ISSUER, 'aud': AUDIENCE, 'iat': now, 'exp': now + 60}
    sin_firma = jwt.encode(claims, key=None, algorithm='none', headers={'kid': 'test-kid-1'})
    hmac = jwt.encode(claims, 'secreto-adivinado-de-al-menos-32-bytes!!', algorithm='HS256',
                      headers={'kid': 'test-kid-1'})
    for t in (sin_firma, hmac, 'no-es-un-jwt', ''):
        with pytest.raises(TokenInvalido):
            verifier.verify(t)


def test_claims_obligatorios(firmante, verifier):
    sin_sub = jwt.encode({'iss': ISSUER, 'aud': AUDIENCE, 'iat': int(time.time()), 'exp': int(time.time()) + 60},
                         firmante.private_key, algorithm='RS256', headers={'kid': firmante.kid})
    with pytest.raises(TokenInvalido):
        verifier.verify(sin_sub)
    with pytest.raises(TokenInvalido):
        verifier.verify(firmante.token(''))


def test_configuracion_incompleta_falla():
    with pytest.raises(ValueError):
        TokenVerifier('', AUDIENCE, lambda t: None)
    with pytest.raises(ValueError):
        TokenVerifier(ISSUER, '', lambda t: None)


def test_api_sin_configuracion_oidc_falla_cerrada(monkeypatch):
    """Sin OIDC_ISSUER/OIDC_AUDIENCE la v2 responde 503, nunca deja pasar."""
    from fastapi.testclient import TestClient

    from app import auth
    from app.config import settings
    from app.main import create_app

    monkeypatch.setattr(settings, 'oidc_issuer', '')
    monkeypatch.setattr(settings, 'oidc_audience', '')
    auth._verifier_from_settings.cache_clear()
    r = TestClient(create_app(settings)).get('/api/v2/me', headers={'Authorization': 'Bearer x.y.z'})
    assert r.status_code == 503
