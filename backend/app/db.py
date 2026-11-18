from collections.abc import Iterator
from functools import lru_cache
from pathlib import Path

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Base

LOCAL_PGDATA = Path(__file__).resolve().parent.parent / ".pgdata"
_local_server = None  # keep a reference so the embedded server stays up for this process


def _local_database_url() -> str:
    global _local_server
    import pgserver  # dev dependency: embedded Postgres with pgvector

    _local_server = pgserver.get_server(LOCAL_PGDATA, cleanup_mode="stop")
    return _local_server.get_uri()


@lru_cache
def get_engine() -> Engine:
    if not settings.database_url:
        raise RuntimeError(
            "DATABASE_URL is not set. Use DATABASE_URL=local for a local database, "
            "or paste your Neon connection string into backend/.env."
        )
    url = _local_database_url() if settings.database_url == "local" else settings.database_url
    url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    url = url.replace("postgres://", "postgresql+psycopg://", 1)
    return create_engine(url, pool_pre_ping=True)


def init_db() -> None:
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    Base.metadata.create_all(engine)
    with engine.begin() as conn:
        conn.execute(
            text("CREATE INDEX IF NOT EXISTS ix_jobs_embedding ON jobs USING hnsw (embedding vector_cosine_ops)")
        )


def session_dependency() -> Iterator[Session]:
    with Session(get_engine()) as session:
        yield session
