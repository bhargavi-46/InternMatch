from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Literal

import numpy as np
from fastapi import Depends, FastAPI, File, HTTPException, Query, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from pypdf.errors import PdfReadError
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import agent
from app.config import settings
from app.db import init_db, session_dependency
from app.embeddings import embed_documents, warm_up
from app.llm import LLMNotConfigured
from app.models import Job
from app.profile import StudentProfile
from app.ranking import SearchFilters, match_profile, score_job, search
from app.ratelimit import llm_rate_limit
from app.resume import parse_resume, pdf_to_text

MAX_RESUME_BYTES = 5 * 1024 * 1024


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    warm_up()
    yield


app = FastAPI(title="InternMatch API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(LLMNotConfigured)
def llm_not_configured(_: Request, exc: LLMNotConfigured) -> JSONResponse:
    return JSONResponse(status_code=503, content={"detail": str(exc)})


class JobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company: str
    title: str
    location: str
    is_remote: bool
    experience_level: str
    min_years_experience: int | None
    url: str
    posted_at: datetime | None
    source: str


class JobDetail(JobOut):
    description: str


class SearchRequest(BaseModel):
    query: str = Field(min_length=2, max_length=300)
    filters: SearchFilters = SearchFilters()
    limit: int = Field(20, ge=1, le=50)


class SearchHitOut(BaseModel):
    job: JobOut
    score: float


class MatchRequest(BaseModel):
    profile: StudentProfile
    filters: SearchFilters = SearchFilters()
    liked_ids: list[int] = Field(default_factory=list, max_length=200)
    hidden_ids: list[int] = Field(default_factory=list, max_length=500)
    limit: int = Field(20, ge=1, le=50)


class MatchOut(BaseModel):
    job: JobOut
    score: float
    semantic: float
    skill_coverage: float
    matched_skills: list[str]
    missing_skills: list[str]


class ExplainRequest(BaseModel):
    profile: StudentProfile


class ChatRequest(BaseModel):
    thread_id: str = Field(min_length=8, max_length=64)
    message: str = Field(min_length=1, max_length=2000)
    profile: StudentProfile | None = None


class ChatReply(BaseModel):
    reply: str


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/stats")
def stats(db: Session = Depends(session_dependency)) -> dict:
    active = select(Job).where(Job.is_active).subquery()
    levels = dict(db.execute(select(active.c.experience_level, func.count()).group_by(active.c.experience_level)).all())
    return {
        "active_jobs": sum(levels.values()),
        "internships": levels.get("internship", 0),
        "entry_level": levels.get("entry_level", 0),
        "companies": db.scalar(select(func.count(func.distinct(active.c.company)))),
        "last_refreshed": db.scalar(select(func.max(Job.last_seen_at))),
    }


@app.get("/jobs", response_model=list[JobOut])
def list_jobs(
    level: Literal["internship", "entry_level", "other"] | None = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(session_dependency),
) -> list[Job]:
    stmt = select(Job).where(Job.is_active).order_by(Job.posted_at.desc().nulls_last()).limit(limit).offset(offset)
    if level:
        stmt = stmt.where(Job.experience_level == level)
    return list(db.scalars(stmt))


def _get_job(db: Session, job_id: int) -> Job:
    job = db.get(Job, job_id)
    if job is None:
        raise HTTPException(404, "Job not found")
    return job


@app.get("/jobs/{job_id}", response_model=JobDetail)
def get_job(job_id: int, db: Session = Depends(session_dependency)) -> Job:
    return _get_job(db, job_id)


@app.post("/search", response_model=list[SearchHitOut])
def search_jobs(body: SearchRequest, db: Session = Depends(session_dependency)) -> list[dict]:
    return [{"job": h.job, "score": h.score} for h in search(db, body.query, body.filters, body.limit)]


@app.post("/match", response_model=list[MatchOut])
def match(body: MatchRequest, db: Session = Depends(session_dependency)) -> list[dict]:
    matches = match_profile(db, body.profile, body.filters, body.liked_ids, body.hidden_ids, body.limit)
    return [m.__dict__ for m in matches]


@app.post("/resume/parse", response_model=StudentProfile, dependencies=[Depends(llm_rate_limit)])
async def resume_parse(file: UploadFile = File(...)) -> StudentProfile:
    data = await file.read(MAX_RESUME_BYTES + 1)
    if len(data) > MAX_RESUME_BYTES:
        raise HTTPException(413, "Resume must be under 5 MB.")
    if not data.startswith(b"%PDF"):
        raise HTTPException(400, "Please upload a PDF resume.")
    try:
        text = pdf_to_text(data)
    except PdfReadError:
        raise HTTPException(400, "Could not read this PDF.") from None
    if len(text.strip()) < 100:
        raise HTTPException(400, "No text found in this PDF. Scanned resumes are not supported yet.")
    # The resume is processed in memory and never stored.
    return parse_resume(text)


@app.post("/jobs/{job_id}/explain", response_model=agent.FitExplanation, dependencies=[Depends(llm_rate_limit)])
def explain(job_id: int, body: ExplainRequest, db: Session = Depends(session_dependency)) -> agent.FitExplanation:
    job = _get_job(db, job_id)
    semantic = 0.0
    if job.embedding is not None:
        semantic = float(np.dot(embed_documents([body.profile.matching_text()])[0], job.embedding))
    match_ = score_job(job, semantic, body.profile.skill_set(), datetime.now(timezone.utc))
    return agent.explain_fit(body.profile, job, match_)


@app.post("/agent/chat", response_model=ChatReply, dependencies=[Depends(llm_rate_limit)])
def agent_chat(body: ChatRequest) -> ChatReply:
    return ChatReply(reply=agent.chat(body.profile, body.thread_id, body.message))
