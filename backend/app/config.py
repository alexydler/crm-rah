from uuid import UUID

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = 'postgresql+psycopg://rah_dev:dev_only_change_me@localhost:5432/rah_vzla'
    s3_endpoint: str = 'http://localhost:9000'
    s3_public_endpoint: str = 'http://localhost:9000'
    s3_access_key: str = 'rah_dev'
    s3_secret_key: str = 'dev_only_change_me_123'
    s3_bucket: str = 'rah-vzla-media'
    s3_url_expira_segundos: int = 900
    cors_origins: str = 'http://localhost:3000,http://127.0.0.1:3000'

    # --- OIDC (Keycloak local en desarrollo). Sin issuer/audience la API v2 falla cerrada (503).
    # OIDC_ISSUER debe coincidir EXACTAMENTE con el claim `iss` (URL vista por el navegador),
    # mientras que OIDC_JWKS_URL puede apuntar a la red interna de Docker.
    oidc_issuer: str = ''
    oidc_audience: str = ''
    oidc_jwks_url: str = ''  # por defecto: {issuer}/protocol/openid-connect/certs (Keycloak)
    oidc_leeway_segundos: int = 30

    # --- API v1 (prototipo monoempresa sin autenticación). Deshabilitada por defecto.
    enable_v1_demo: bool = False
    # Si se habilita v1, se acota a esta organización DEMO (RLS) y nunca a datos de agencias.
    v1_demo_organizacion_id: UUID | None = None

    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

    @property
    def jwks_url(self) -> str:
        if self.oidc_jwks_url:
            return self.oidc_jwks_url
        return f"{self.oidc_issuer.rstrip('/')}/protocol/openid-connect/certs" if self.oidc_issuer else ''


settings = Settings()
