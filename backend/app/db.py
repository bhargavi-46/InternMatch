import atexit
import logging
import os
import subprocess
import sys
import time
from collections.abc import Iterator
from functools import lru_cache
from pathlib import Path

from sqlalchemy import Engine, create_engine, or_, select, text, update
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Base, Job

log = logging.getLogger("db")

# Kept outside the project folder: sync tools such as OneDrive lock database files and slow Postgres down.
LOCAL_ROOT = Path(os.environ.get("LOCALAPPDATA") or Path.home() / ".local" / "share") / "InternMatch"
LOCAL_PGDATA = LOCAL_ROOT / "pgdata"
LOCAL_PGLOG = LOCAL_ROOT / "postgres.log"  # outside the data folder, so crash recovery never trips over it
START_TIMEOUT = 180  # seconds; recovery after an unclean stop can take a while on slow disks


def _running_postmaster():
    from pgserver.utils import PostmasterInfo

    info = PostmasterInfo.read_from_pgdata(LOCAL_PGDATA)
    if info is None or not info.is_running() or "postgres" not in info.process.name().lower():
        return None  # missing, or a stale postmaster.pid left by a crash
    return info


def _stop_local_postgres() -> None:
    import pgserver

    try:
        pgserver.pg_ctl(["-m", "fast", "-w", "stop"], pgdata=LOCAL_PGDATA, timeout=60)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        log.warning("Could not stop the local database cleanly; it will recover on the next start.")


def _local_database_url() -> str:
    """Start (or reuse) an embedded Postgres + pgvector server and return its URL."""
    import pgserver  # dev dependency: embedded Postgres with pgvector
    from pgserver.utils import find_suitable_port

    LOCAL_ROOT.mkdir(parents=True, exist_ok=True)
    if not (LOCAL_PGDATA / "PG_VERSION").exists():
        log.info("Creating local database in %s", LOCAL_PGDATA)
        pgserver.initdb(["--auth=trust", "--encoding=utf8", "-U", "postgres"], pgdata=LOCAL_PGDATA)

    if _running_postmaster() is None:
        log.info("Starting local database (this can take a minute after an unclean stop)...")
        # Detach Postgres from this terminal so Ctrl+C stops only the app, not the database processes.
        detach = (
            {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS}
            if sys.platform == "win32"
            else {"start_new_session": True}
        )
        port = find_suitable_port("127.0.0.1")
        args = ["-w", "-t", str(START_TIMEOUT), "-o", '-h "127.0.0.1"', "-o", f"-p {port}", "-l", str(LOCAL_PGLOG)]
        try:
            pgserver.pg_ctl([*args, "start"], pgdata=LOCAL_PGDATA, timeout=START_TIMEOUT + 30, **detach)
        except subprocess.CalledProcessError as exc:
            raise RuntimeError(f"Local database failed to start. See the log: {LOCAL_PGLOG}") from exc
        atexit.register(_stop_local_postgres)  # only the process that started the server stops it

    deadline = time.monotonic() + START_TIMEOUT
    while (info := _running_postmaster()) is None or info.status != "ready":
        if time.monotonic() > deadline:
            raise RuntimeError(f"Local database did not become ready. See the log: {LOCAL_PGLOG}")
        time.sleep(1)
    return info.get_uri()


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
        # create_all() does not add columns to an existing table, so add the ones introduced later.
        for column, kind in NEW_COLUMNS.items():
            conn.execute(text(f"ALTER TABLE jobs ADD COLUMN IF NOT EXISTS {column} {kind}"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_jobs_role_family ON jobs (role_family)"))
    retag_jobs(engine)


NEW_COLUMNS = {"role_family": "varchar(20)", "duration_months": "integer", "start_month": "varchar(20)",
               "tags_version": "integer"}


def retag_jobs(engine: Engine) -> int:
    """Recompute experience level and tags for jobs tagged by older rules (or never tagged). Fast: pure Python on
    ~thousands of rows."""
    from app.ingest.filters import classify_level, min_years_experience
    from app.ingest.tags import TAGS_VERSION, job_tags

    def fresh(r) -> dict:
        level = classify_level(r.title, r.description, r.employment_type)
        return {"id": r.id, "experience_level": level, "min_years_experience": min_years_experience(r.description, r.title),
                **job_tags(r.title, r.description, level)}

    with Session(engine) as session, session.begin():
        stale = session.execute(
            select(Job.id, Job.title, Job.description, Job.employment_type).where(
                or_(Job.tags_version.is_(None), Job.tags_version != TAGS_VERSION)
            )
        ).all()
        if stale:
            session.execute(update(Job), [fresh(r) for r in stale])
    if stale:
        log.info("Re-tagged %d jobs", len(stale))
    return len(stale)


def session_dependency() -> Iterator[Session]:
    with Session(get_engine()) as session:
        yield session
