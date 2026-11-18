from sqlalchemy import select
from sqlalchemy.orm import Session

from app.embeddings import embed_documents, job_text
from app.models import Job

BATCH_SIZE = 64


def embed_pending(session: Session) -> int:
    """Embed every active job that has no embedding yet (new or edited postings). Returns the count."""
    done = 0
    while True:
        jobs = list(
            session.scalars(
                select(Job).where(Job.is_active, Job.embedding.is_(None)).order_by(Job.id).limit(BATCH_SIZE)
            )
        )
        if not jobs:
            return done
        for job, vector in zip(jobs, embed_documents([job_text(j) for j in jobs])):
            job.embedding = vector
        session.commit()
        done += len(jobs)
