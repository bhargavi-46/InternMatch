"""Fetch jobs from public company job boards and upsert the relevant ones into Postgres.

Usage (from backend/):
    uv run python -m app.ingest.run --dry-run   # fetch + filter, print a summary only
    uv run python -m app.ingest.run             # also write to the database
"""

import argparse
import asyncio
import dataclasses
import hashlib
import logging
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone

import httpx
from sqlalchemy import ColumnElement, and_, case, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.db import get_engine, init_db
from app.ingest.boards import BOARDS, Board
from app.ingest.embed import embed_pending
from app.ingest.filters import experience_level, is_relevant_location, min_years_experience
from app.ingest.sources import FETCHERS, Posting
from app.models import Job

log = logging.getLogger("ingest")

UPDATED_COLUMNS = [
    "company", "title", "location", "is_remote", "employment_type", "experience_level",
    "min_years_experience", "description", "url", "posted_at", "last_seen_at", "is_active", "content_hash",
]


@dataclass
class Batch:
    name: str
    postings: list[Posting] | None  # None means the fetch failed
    stale: ColumnElement[bool]  # saved jobs in this batch's scope to deactivate after saving


def _describe(exc: Exception) -> str:
    # Short, URL-free messages keep the log readable.
    if isinstance(exc, httpx.HTTPStatusError):
        return f"HTTP {exc.response.status_code}"
    return type(exc).__name__


async def fetch_all(started: datetime) -> list[Batch]:
    limit = asyncio.Semaphore(8)
    async with httpx.AsyncClient(timeout=30, headers={"User-Agent": "InternMatch/0.1"}) as client:

        async def fetch_board(board: Board) -> Batch:
            stale = and_(Job.source == board.source, Job.company == board.company, Job.last_seen_at < started)
            async with limit:
                try:
                    postings = await FETCHERS[board.source](client, board.slug, board.company)
                except (httpx.HTTPError, KeyError, ValueError) as exc:
                    log.warning("skipping %s/%s: %s", board.source, board.slug, _describe(exc))
                    postings = None
            return Batch(board.company, postings, stale)

        return await asyncio.gather(*(fetch_board(b) for b in BOARDS))


def to_row(posting: Posting, seen_at: datetime) -> dict:
    content = f"{posting.title}\n{posting.description}"
    return {
        "source": posting.source,
        "external_id": posting.external_id,
        "company": posting.company,
        "title": posting.title[:300],
        "location": posting.location[:500],
        "is_remote": posting.is_remote,
        "employment_type": posting.employment_type,
        "experience_level": experience_level(posting),
        "min_years_experience": min_years_experience(posting.description),
        "description": posting.description,
        "url": posting.url,
        "posted_at": posting.posted_at,
        "last_seen_at": seen_at,
        "is_active": True,
        "content_hash": hashlib.sha256(content.encode()).hexdigest(),
    }


def save(batches: list[Batch], started: datetime) -> None:
    init_db()
    with Session(get_engine()) as session, session.begin():
        for batch in batches:
            if batch.postings is None:
                continue  # fetch failed: keep this batch's existing jobs as they are
            if batch.postings:
                stmt = insert(Job).values([to_row(p, started) for p in batch.postings])
                new = stmt.excluded
                set_ = {col: new[col] for col in UPDATED_COLUMNS}
                set_["embedding"] = case((Job.content_hash == new.content_hash, Job.embedding), else_=None)
                session.execute(stmt.on_conflict_do_update(index_elements=["source", "external_id"], set_=set_))
            session.execute(update(Job).where(batch.stale).values(is_active=False))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dry-run", action="store_true", help="fetch and filter only; do not touch the database")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)  # one log line per request is too noisy

    started = datetime.now(timezone.utc)
    fetched = asyncio.run(fetch_all(started))
    relevant = [
        # Only http(s) links: job URLs are rendered as links in the browser.
        dataclasses.replace(
            b, postings=[p for p in b.postings if is_relevant_location(p) and p.url.startswith(("https://", "http://"))]
        )
        if b.postings is not None
        else b
        for b in fetched
    ]

    totals: Counter[str] = Counter()
    for raw, kept in zip(fetched, relevant):
        if kept.postings is None:
            continue
        levels = Counter(experience_level(p) for p in kept.postings)
        totals.update(levels)
        print(
            f"{kept.name:<12} fetched {len(raw.postings):>4}  kept {len(kept.postings):>3}  "
            f"(internship {levels['internship']}, entry {levels['entry_level']})"
        )
    print(
        f"\nTotal kept: {sum(totals.values())}  internship {totals['internship']}  "
        f"entry {totals['entry_level']}  other {totals['other']}"
    )

    if not args.dry_run:
        save(relevant, started)
        print("Saved to database. Embedding new and edited postings...")
        with Session(get_engine()) as session:
            print(f"Embedded {embed_pending(session)} postings.")


if __name__ == "__main__":
    main()
