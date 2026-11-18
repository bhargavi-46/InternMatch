from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, String, Text, UniqueConstraint, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

EMBEDDING_DIM = 384


class Base(DeclarativeBase):
    pass


class Job(Base):
    __tablename__ = "jobs"
    __table_args__ = (UniqueConstraint("source", "external_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    source: Mapped[str] = mapped_column(String(20))
    external_id: Mapped[str] = mapped_column(String(100))
    company: Mapped[str] = mapped_column(String(100), index=True)
    title: Mapped[str] = mapped_column(String(300))
    location: Mapped[str] = mapped_column(String(500))
    is_remote: Mapped[bool]
    employment_type: Mapped[str | None] = mapped_column(String(50))
    experience_level: Mapped[str] = mapped_column(String(20), index=True)
    min_years_experience: Mapped[int | None]
    # Tags from app/ingest/tags.py
    role_family: Mapped[str | None] = mapped_column(String(20), index=True)
    duration_months: Mapped[int | None]
    start_month: Mapped[str | None] = mapped_column(String(20))
    tags_version: Mapped[int | None]
    description: Mapped[str] = mapped_column(Text)
    url: Mapped[str] = mapped_column(String(1000))
    posted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(default=True, index=True)
    # Embedding is cleared whenever the hash changes, so edited postings get re-embedded.
    content_hash: Mapped[str] = mapped_column(String(64))
    embedding: Mapped[list[float] | None] = mapped_column(Vector(EMBEDDING_DIM))
