"""Evaluate ranking quality (and optionally LLM explanation grounding) on the live index.

Usage (from backend/):
    uv run python -m app.evals.run           # ranking evals: keyword vs semantic vs hybrid vs full ranker
    uv run python -m app.evals.run --llm     # also check that LLM explanations only cite real skills

Every method sees all experience levels, so the score shows whether ranking itself
puts student-friendly roles first. Results are printed and written to eval_results.md.
"""

import argparse
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_engine
from app.evals.metrics import ndcg_at_k, precision_at_k, reciprocal_rank
from app.evals.personas import PERSONAS, Persona
from app.models import Job
from app.ranking import (
    SearchFilters,
    keyword_candidates,
    match_profile,
    profile_vector,
    reciprocal_rank_fusion,
    score_job,
    semantic_candidates,
)
from app.skills import extract_skills

K = 10
ALL_LEVELS = SearchFilters(levels=[], role_families=[])
GAIN = {"internship": 2, "entry_level": 1}
RESULTS_FILE = Path(__file__).resolve().parents[2] / "eval_results.md"


def gain(persona: Persona, job: Job) -> int:
    return GAIN.get(job.experience_level, 0) if persona.role_pattern.search(job.title) else 0


def rank_keyword(session: Session, persona: Persona) -> list[Job]:
    return [j for j, _ in keyword_candidates(session, persona.profile.keyword_query(), ALL_LEVELS, K)]


def rank_semantic(session: Session, persona: Persona) -> list[Job]:
    return [j for j, _ in semantic_candidates(session, profile_vector(session, persona.profile), ALL_LEVELS, K)]


def rank_hybrid(session: Session, persona: Persona) -> list[Job]:
    semantic = semantic_candidates(session, profile_vector(session, persona.profile), ALL_LEVELS, 100)
    keyword = keyword_candidates(session, persona.profile.keyword_query(), ALL_LEVELS, 100)
    jobs = {j.id: j for j, _ in semantic + keyword}
    fused = reciprocal_rank_fusion([j.id for j, _ in semantic], [j.id for j, _ in keyword])
    return [jobs[i] for i in sorted(fused, key=fused.__getitem__, reverse=True)[:K]]


def rank_full(session: Session, persona: Persona) -> list[Job]:
    return [m.job for m in match_profile(session, persona.profile, ALL_LEVELS, limit=K)]


METHODS: dict[str, Callable[[Session, Persona], list[Job]]] = {
    "Keyword (Postgres full-text)": rank_keyword,
    "Semantic (pgvector)": rank_semantic,
    "Hybrid (RRF)": rank_hybrid,
    "InternMatch ranker": rank_full,
}


def ranking_evals(session: Session) -> list[str]:
    active = list(session.scalars(select(Job).where(Job.is_active, Job.embedding.is_not(None))))
    lines = [
        f"Index: {len(active)} active jobs. Relevant = title matches the persona's role AND the job is an "
        "internship (gain 2) or entry-level (gain 1).",
        "",
    ]
    scored = []
    for persona in PERSONAS:
        ideal = [g for g in (gain(persona, j) for j in active) if g > 0]
        if ideal:
            scored.append((persona, ideal))
        else:
            lines.append(f"- Skipped persona '{persona.name}': no relevant jobs in the index today.")
    lines += ["", f"Personas evaluated: {len(scored)}", "", "| Method | P@5 | P@10 | nDCG@10 | MRR |", "|---|---|---|---|---|"]
    for name, method in METHODS.items():
        p5, p10, ndcg, mrr = [], [], [], []
        for persona, ideal in scored:
            gains = [gain(persona, job) for job in method(session, persona)]
            gains += [0] * (K - len(gains))
            p5.append(precision_at_k(gains, 5))
            p10.append(precision_at_k(gains, 10))
            ndcg.append(ndcg_at_k(gains, ideal, K))
            mrr.append(reciprocal_rank(gains))
        lines.append(f"| {name} | {mean(p5):.3f} | {mean(p10):.3f} | {mean(ndcg):.3f} | {mean(mrr):.3f} |")
    return lines


def llm_grounding_evals(session: Session, personas: int = 3, jobs_per_persona: int = 3) -> list[str]:
    """An explanation is grounded when every matching skill is in both the profile and the job,
    and every missing skill is in the job but not in the profile."""
    from app.agent import explain_fit

    checked = grounded_claims = total_claims = 0
    scores = []
    for persona in PERSONAS[:personas]:
        profile_text = ", ".join(persona.profile.skills).lower()
        profile_skills = persona.profile.skill_set()
        for match in match_profile(session, persona.profile, SearchFilters(), limit=jobs_per_persona):
            job = match.job
            job_text = f"{job.title}\n{job.description}"
            job_skills = extract_skills(job_text)
            explanation = explain_fit(persona.profile, job, score_job(job, match.semantic, profile_skills, datetime.now(timezone.utc)))
            scores.append(explanation.fit_score)
            checked += 1
            for skill in explanation.matching_skills:
                canonical = extract_skills(skill + ",")
                in_profile = bool(canonical & profile_skills) or skill.lower() in profile_text
                in_job = bool(canonical & job_skills) or skill.lower() in job_text.lower()
                grounded_claims += in_profile and in_job
                total_claims += 1
            for skill in explanation.missing_skills:
                canonical = extract_skills(skill + ",")
                in_profile = bool(canonical & profile_skills) or skill.lower() in profile_text
                in_job = bool(canonical & job_skills) or skill.lower() in job_text.lower()
                grounded_claims += in_job and not in_profile
                total_claims += 1
    rate = grounded_claims / total_claims if total_claims else 0.0
    return [
        "",
        "## LLM explanation grounding",
        "",
        f"Explanations checked: {checked}. Skill claims checked: {total_claims}.",
        f"Grounded claims: {grounded_claims} ({rate:.1%}). Mean fit score: {mean(scores):.1f}/10." if scores else "",
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--llm", action="store_true", help="also run LLM grounding evals (uses your Groq key)")
    args = parser.parse_args()

    with Session(get_engine()) as session:
        lines = ["# InternMatch eval results", "", f"Run: {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC", ""]
        lines += ranking_evals(session)
        if args.llm:
            lines += llm_grounding_evals(session)
    report = "\n".join(lines) + "\n"
    print(report)
    RESULTS_FILE.write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()
