import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# Interpret the config file for Python logging.
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Obtener URL de conexión desde variables de entorno
def get_database_url() -> str:
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        # Asegurar driver compatible con psycopg v3 o v2
        if db_url.startswith("postgresql://") and not db_url.startswith("postgresql+"):
            db_url = db_url.replace("postgresql://", "postgresql+psycopg://", 1)
        return db_url

    user = os.getenv("POSTGRES_USER", "rah_dev")
    password = os.getenv("POSTGRES_PASSWORD", "dev_only_change_me")
    host = os.getenv("POSTGRES_HOST", "127.0.0.1")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB", "rah_vzla")
    return f"postgresql+psycopg://{user}:{password}@{host}:{port}/{db}"

target_metadata = None


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = get_database_url()

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
