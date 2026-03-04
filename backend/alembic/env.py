from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import Base
import app.models  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# Railway injects DATABASE_URL; local dev uses SYNC_DATABASE_URL
# Also try individual PG* vars that Railway's PostgreSQL plugin always injects
def _url_from_pg_vars() -> str:
    host = os.getenv("PGHOST") or os.getenv("RAILWAY_TCP_PROXY_DOMAIN")
    port = os.getenv("PGPORT") or os.getenv("RAILWAY_TCP_PROXY_PORT") or "5432"
    user = os.getenv("PGUSER")
    password = os.getenv("PGPASSWORD")
    db = os.getenv("PGDATABASE")
    if all([host, user, password, db]):
        return f"postgresql://{user}:{password}@{host}:{port}/{db}"
    return ""


_raw_url = (
    os.getenv("SYNC_DATABASE_URL")
    or os.getenv("DATABASE_URL")
    or os.getenv("DATABASE_PRIVATE_URL")
    or _url_from_pg_vars()
    or "postgresql://ghost:protocol@localhost:5432/ghostprotocol"
)
# Strip async driver suffix so psycopg2 (sync) can use it
database_url = (
    _raw_url
    .replace("postgres://", "postgresql://", 1)
    .replace("postgresql+asyncpg://", "postgresql://")
)
print(f"[alembic] Using database host: {database_url.split('@')[-1] if '@' in database_url else 'unknown'}")
config.set_main_option("sqlalchemy.url", database_url)


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
