from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = 'postgresql+psycopg://rah_dev:dev_only_change_me@localhost:5432/rah_vzla'
    s3_endpoint: str = 'http://localhost:9000'
    s3_public_endpoint: str = 'http://localhost:9000'
    s3_access_key: str = 'rah_dev'
    s3_secret_key: str = 'dev_only_change_me_123'
    s3_bucket: str = 'rah-vzla-media'
    cors_origins: str = 'http://localhost:3000,http://127.0.0.1:3000'
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')


settings = Settings()
