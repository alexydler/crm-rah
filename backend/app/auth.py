"""Verificación de access tokens OIDC (Bearer) contra el JWKS del proveedor (Keycloak local).

Comprueba firma (solo RS256/ES256, nunca `none` ni HMAC), `iss`, `aud`, `exp`, `iat` y `sub`.
No hay autenticación por cabeceras ni contraseñas caseras.
"""
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any, Protocol

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .config import settings

ALGORITMOS_PERMITIDOS = ['RS256', 'ES256']
_WWW = {'WWW-Authenticate': 'Bearer'}


@dataclass(frozen=True)
class Usuario:
    sub: str
    email: str | None = None
    nombre: str | None = None
    claims: dict[str, Any] = field(default_factory=dict, repr=False, compare=False)


class KeyResolver(Protocol):
    def __call__(self, token: str) -> Any: ...


class TokenInvalido(Exception):
    pass


class ProveedorNoDisponible(Exception):
    """No se pudo obtener el JWKS: no es culpa del token, no debe responder 401."""


class TokenVerifier:
    def __init__(self, issuer: str, audience: str, key_resolver: KeyResolver, leeway: int = 30):
        if not issuer or not audience:
            raise ValueError('OIDC_ISSUER y OIDC_AUDIENCE son obligatorios')
        self.issuer = issuer
        self.audience = audience
        self.key_resolver = key_resolver
        self.leeway = leeway

    def verify(self, token: str) -> Usuario:
        try:
            header = jwt.get_unverified_header(token)
            if header.get('alg') not in ALGORITMOS_PERMITIDOS:
                raise TokenInvalido('Algoritmo no permitido')
            key = self.key_resolver(token)
            claims = jwt.decode(
                token, key=key, algorithms=ALGORITMOS_PERMITIDOS,
                audience=self.audience, issuer=self.issuer, leeway=self.leeway,
                options={'require': ['exp', 'iat', 'iss', 'aud', 'sub']},
            )
        except TokenInvalido:
            raise
        except jwt.PyJWKClientConnectionError:
            raise ProveedorNoDisponible() from None
        except (jwt.PyJWTError, ValueError, KeyError) as exc:
            raise TokenInvalido(type(exc).__name__) from None
        sub = claims.get('sub')
        if not isinstance(sub, str) or not sub:
            raise TokenInvalido('sub vacío')
        return Usuario(
            sub=sub, email=claims.get('email'),
            nombre=claims.get('name') or claims.get('preferred_username'), claims=claims,
        )


def jwks_key_resolver(jwks_url: str) -> KeyResolver:
    client = jwt.PyJWKClient(jwks_url, cache_keys=True, lifespan=300, timeout=5)

    def resolve(token: str):
        return client.get_signing_key_from_jwt(token).key

    return resolve


@lru_cache(maxsize=1)
def _verifier_from_settings() -> TokenVerifier:
    if not settings.oidc_issuer or not settings.oidc_audience or not settings.jwks_url:
        raise ValueError('Configuración OIDC incompleta')
    return TokenVerifier(
        settings.oidc_issuer, settings.oidc_audience, jwks_key_resolver(settings.jwks_url),
        leeway=settings.oidc_leeway_segundos,
    )


def get_token_verifier() -> TokenVerifier:
    """Dependencia sustituible en tests (dependency_overrides) por un verificador con JWKS local."""
    try:
        return _verifier_from_settings()
    except ValueError:
        # Falla cerrada: sin configuración OIDC no se atiende ninguna ruta v2.
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, 'Autenticación no configurada') from None


_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    verifier: TokenVerifier = Depends(get_token_verifier),
) -> Usuario:
    if credentials is None or credentials.scheme.lower() != 'bearer' or not credentials.credentials:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, 'No autenticado', headers=_WWW)
    try:
        return verifier.verify(credentials.credentials)
    except TokenInvalido:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, 'Token inválido o expirado', headers=_WWW) from None
    except ProveedorNoDisponible:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, 'Proveedor de identidad no disponible') from None
