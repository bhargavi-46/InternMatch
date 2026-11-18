"""Retrieval and ranking.

search():        hybrid retrieval (pgvector semantic + Postgres full-text), fused with reciprocal rank fusion.
match_profile(): personalised ranking for a student profile:
                 1. retrieve candidates by embedding similarity (plus keyword hits on roles and skills),
                 2. re-rank with semantic fit, skill coverage, experience level and recency,
                 3. personalise the query vector from liked / hidden jobs (Rocchio feedback).
"""

import math
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Literal

import numpy as np
from pydantic import BaseModel, Field
from sqlalchemy import Select, func, or_, select, text
from sqlalchemy.orm import Session

from app.embeddings import embed_documents, embed_query, normalize
from app.ingest.tags import TECH_FAMILIES, RoleFamily
from app.models import Job
from app.profile import StudentProfile
from app.skills import extract_skills

Level = Literal["internship", "entry_level", "other"]

# Picked by a small sweep on the eval personas (see app/evals); skills mostly drive the explanation, not the order.
WEIGHTS = {"semantic": 0.60, "skills": 0.10, "level": 0.25, "recency": 0.05}
LEVEL_SCORE = {"internship": 1.0, "entry_level": 0.8, "other": 0.2}
LIKED_WEIGHT = 0.35
HIDDEN_WEIGHT = 0.20


class SearchFilters(BaseModel):
    levels: list[Level] = ["internship", "entry_level"]
    remote_only: bool = False
    location: str | None = None
    max_years_experience: int | None = None
    # Empty means every role family. The default hides non-technical roles (marketing, finance, HR...).
    role_families: list[RoleFamily] = list(TECH_FAMILIES)
    min_duration_months: int | None = Field(None, ge=1, le=12)  # internships that state at least this length
    posted_within_days: int | None = Field(None, ge=1, le=365)


@dataclass
class Hit:
    job: Job
    score: float


@dataclass
class Match:
    job: Job
    score: float
    semantic: float
    skill_coverage: float
    matched_skills: list[str]
    missing_skills: list[str]


def _filtered(filters: SearchFilters, exclude_ids: Iterable[int] = ()) -> Select:
    stmt = select(Job).where(Job.is_active, Job.embedding.is_not(None))
    if filters.levels:
        stmt = stmt.where(Job.experience_level.in_(filters.levels))
    if filters.remote_only:
        stmt = stmt.where(Job.is_remote)
    if filters.location:
        stmt = stmt.where(or_(Job.location.ilike(f"%{filters.location}%"), Job.is_remote))
    if filters.max_years_experience is not None:
        stmt = stmt.where(
            or_(Job.min_years_experience.is_(None), Job.min_years_experience <= filters.max_years_experience)
        )
    if filters.role_families:
        family = Job.role_family.in_(filters.role_families)
        # Jobs not tagged yet count as "other".
        stmt = stmt.where(or_(family, Job.role_family.is_(None)) if "other" in filters.role_families else family)
    if filters.min_duration_months is not None:
        stmt = stmt.where(Job.duration_months >= filters.min_duration_months)
    if filters.posted_within_days is not None:
        since = datetime.now(timezone.utc) - timedelta(days=filters.posted_within_days)
        stmt = stmt.where(Job.posted_at >= since)
    excluded = list(exclude_ids)
    if excluded:
        stmt = stmt.where(Job.id.not_in(excluded))
    return stmt


def semantic_candidates(
    session: Session, vector: np.ndarray, filters: SearchFilters, k: int, exclude_ids: Iterable[int] = ()
) -> list[tuple[Job, float]]:
    # HNSW returns at most ef_search rows before filtering; raise it so filters don't starve results.
    session.execute(text("SET LOCAL hnsw.ef_search = 400"))
    distance = Job.embedding.cosine_distance(vector)
    stmt = _filtered(filters, exclude_ids).add_columns(distance.label("distance")).order_by(distance).limit(k)
    return [(job, 1.0 - float(dist)) for job, dist in session.execute(stmt)]


def keyword_candidates(
    session: Session, query: str, filters: SearchFilters, k: int, exclude_ids: Iterable[int] = ()
) -> list[tuple[Job, float]]:
    if not query.strip():
        return []
    document = func.to_tsvector("english", func.concat(Job.title, " ", Job.description))
    tsquery = func.websearch_to_tsquery("english", query)
    rank = func.ts_rank_cd(document, tsquery)
    stmt = (
        _filtered(filters, exclude_ids)
        .add_columns(rank.label("rank"))
        .where(document.op("@@")(tsquery))
        .order_by(rank.desc())
        .limit(k)
    )
    return [(job, float(r)) for job, r in session.execute(stmt)]


def reciprocal_rank_fusion(*rankings: list[int], k: int = 60) -> dict[int, float]:
    scores: dict[int, float] = defaultdict(float)
    for ranking in rankings:
        for position, job_id in enumerate(ranking):
            scores[job_id] += 1.0 / (k + position + 1)
    return scores


def search(session: Session, query: str, filters: SearchFilters, limit: int = 20) -> list[Hit]:
    semantic = semantic_candidates(session, embed_query(query), filters, k=100)
    keyword = keyword_candidates(session, query, filters, k=100)
    jobs = {job.id: job for job, _ in semantic + keyword}
    fused = reciprocal_rank_fusion([j.id for j, _ in semantic], [j.id for j, _ in keyword])
    ranked = sorted(fused, key=fused.__getitem__, reverse=True)[:limit]
    return [Hit(jobs[job_id], fused[job_id]) for job_id in ranked]


def _mean_embedding(session: Session, job_ids: Iterable[int]) -> np.ndarray | None:
    ids = list(job_ids)
    if not ids:
        return None
    rows = session.scalars(select(Job.embedding).where(Job.id.in_(ids), Job.embedding.is_not(None))).all()
    return np.mean(np.array(rows), axis=0) if rows else None


def profile_vector(
    session: Session, profile: StudentProfile, liked_ids: Iterable[int] = (), hidden_ids: Iterable[int] = ()
) -> np.ndarray:
    vector = embed_documents([profile.matching_text()])[0]
    liked = _mean_embedding(session, liked_ids)
    hidden = _mean_embedding(session, hidden_ids)
    if liked is not None:
        vector = vector + LIKED_WEIGHT * liked
    if hidden is not None:
        vector = vector - HIDDEN_WEIGHT * hidden
    return normalize(vector)


def score_job(job: Job, semantic: float, profile_skills: set[str], now: datetime) -> Match:
    job_skills = extract_skills(f"{job.title}\n{job.description}")
    matched = job_skills & profile_skills
    coverage = len(matched) / len(job_skills) if job_skills else 0.0
    # bge cosine similarities for related texts sit roughly between 0.5 and 0.9.
    semantic_scaled = min(max((semantic - 0.5) / 0.4, 0.0), 1.0)
    recency = math.exp(-max((now - job.posted_at).days, 0) / 30) if job.posted_at else 0.5
    score = (
        WEIGHTS["semantic"] * semantic_scaled
        + WEIGHTS["skills"] * coverage
        + WEIGHTS["level"] * LEVEL_SCORE.get(job.experience_level, 0.2)
        + WEIGHTS["recency"] * recency
    )
    return Match(
        job=job,
        score=round(score, 4),
        semantic=round(semantic, 4),
        skill_coverage=round(coverage, 4),
        matched_skills=sorted(matched),
        missing_skills=sorted(job_skills - profile_skills),
    )


def match_profile(
    session: Session,
    profile: StudentProfile,
    filters: SearchFilters,
    liked_ids: Iterable[int] = (),
    hidden_ids: Iterable[int] = (),
    limit: int = 20,
    candidates_k: int = 150,
) -> list[Match]:
    hidden = list(hidden_ids)
    vector = profile_vector(session, profile, liked_ids, hidden)
    candidates = {job.id: (job, sim) for job, sim in semantic_candidates(session, vector, filters, candidates_k, hidden)}
    for job, _ in keyword_candidates(session, profile.keyword_query(), filters, 50, hidden):
        if job.id not in candidates:
            candidates[job.id] = (job, float(np.dot(vector, job.embedding)))
    now = datetime.now(timezone.utc)
    skills = profile.skill_set()
    matches = [score_job(job, sim, skills, now) for job, sim in candidates.values()]
    return sorted(matches, key=lambda m: m.score, reverse=True)[:limit]
