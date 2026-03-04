from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
import os


def _url_from_pg_vars() -> str:
    """Construct a DB URL from individual PG* env vars (Railway always injects these)."""
    host = os.getenv("PGHOST") or os.getenv("RAILWAY_TCP_PROXY_DOMAIN")
    port = os.getenv("PGPORT") or os.getenv("RAILWAY_TCP_PROXY_PORT") or "5432"
    user = os.getenv("PGUSER")
    password = os.getenv("PGPASSWORD")
    db = os.getenv("PGDATABASE")
    if all([host, user, password, db]):
        return f"postgresql://{user}:{password}@{host}:{port}/{db}"
    return ""


def _build_async_url(raw: str) -> str:
    """Convert postgres:// or postgresql:// to postgresql+asyncpg://"""
    if raw.startswith("postgres://"):
        raw = raw.replace("postgres://", "postgresql://", 1)
    if "postgresql://" in raw and "+asyncpg" not in raw:
        raw = raw.replace("postgresql://", "postgresql+asyncpg://", 1)
    return raw


def _build_sync_url(raw: str) -> str:
    """Ensure sync URL uses plain postgresql:// (no driver suffix)"""
    raw = raw.replace("postgres://", "postgresql://", 1)
    raw = raw.replace("postgresql+asyncpg://", "postgresql://")
    return raw


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Railway provides DATABASE_URL; we derive both variants from it
    DATABASE_URL: str = "postgresql+asyncpg://ghost:protocol@localhost:5432/ghostprotocol"
    SYNC_DATABASE_URL: str = "postgresql://ghost:protocol@localhost:5432/ghostprotocol"
    REDIS_URL: str = "redis://localhost:6379"
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "ghostprotocol"
    SECRET_KEY: str = "change-me-in-production-use-a-real-secret-key"
    ANTHROPIC_API_KEY: str = ""
    ENVIRONMENT: str = "development"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    ALGORITHM: str = "HS256"
    # Comma-separated allowed CORS origins (set in Railway env vars)
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    def model_post_init(self, __context):
        # Try all the ways Railway might provide the DB URL
        raw = (
            os.getenv("DATABASE_URL")
            or os.getenv("DATABASE_PRIVATE_URL")
            or _url_from_pg_vars()
            or ""
        )
        if raw and not raw.startswith("postgresql+asyncpg://"):
            object.__setattr__(self, "DATABASE_URL", _build_async_url(raw))
            object.__setattr__(self, "SYNC_DATABASE_URL", _build_sync_url(raw))


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
