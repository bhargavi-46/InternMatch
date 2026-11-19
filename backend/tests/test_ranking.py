from datetime import datetime, timedelta, timezone

import pytest

from app.evals.metrics import ndcg_at_k, precision_at_k, reciprocal_rank
from app.models import Job
from app.ranking import WEIGHTS, SearchFilters, _filtered, reciprocal_rank_fusion, score_job

NOW = datetime(2026, 11, 18, tzinfo=timezone.utc)


def job(level="internship", description="Python and Docker.", posted_days_ago=0, title="Intern"):
    return Job(
        id=1, title=title, company="Acme", description=description, experience_level=level,
        posted_at=NOW - timedelta(days=posted_days_ago),
    )


def test_weights_sum_to_one():
    assert sum(WEIGHTS.values()) == pytest.approx(1.0)


def test_score_reports_matched_and_missing_skills():
    match = score_job(job(description="Python, Docker and Kubernetes."), 0.8, {"Python", "React"}, NOW)
    assert match.matched_skills == ["Python"]
    assert match.missing_skills == ["Docker", "Kubernetes"]
    assert match.skill_coverage == pytest.approx(1 / 3, abs=1e-3)


def test_internship_outranks_senior_role_at_same_similarity():
    intern = score_job(job(level="internship"), 0.75, {"Python"}, NOW)
    senior = score_job(job(level="other"), 0.75, {"Python"}, NOW)
    assert intern.score > senior.score


def test_newer_posting_scores_higher():
    fresh = score_job(job(posted_days_ago=1), 0.75, set(), NOW)
    stale = score_job(job(posted_days_ago=90), 0.75, set(), NOW)
    assert fresh.score > stale.score


def test_reciprocal_rank_fusion_rewards_agreement():
    fused = reciprocal_rank_fusion([1, 2, 3], [2, 4])
    assert max(fused, key=fused.get) == 2
    assert set(fused) == {1, 2, 3, 4}


def test_metrics():
    gains = [0, 2, 0, 1, 0]
    assert precision_at_k(gains, 5) == pytest.approx(0.4)
    assert reciprocal_rank(gains) == pytest.approx(0.5)
    assert ndcg_at_k([2, 1], [2, 1], 2) == pytest.approx(1.0)
    assert 0 < ndcg_at_k(gains, [2, 1], 5) < 1
    assert ndcg_at_k([0, 0], [], 2) == 0.0


def _sql(filters: SearchFilters) -> str:
    sql = str(_filtered(filters).compile(compile_kwargs={"literal_binds": True}))
    return sql.split("WHERE", 1)[1]  # only the conditions


def test_default_filters_hide_non_tech_roles():
    sql = _sql(SearchFilters())
    assert "role_family IN" in sql and "'non_tech'" not in sql and "'swe'" in sql
    assert "role_family IS NULL" in sql  # untagged jobs count as "other"


def test_role_family_filter_without_other_skips_untagged_jobs():
    sql = _sql(SearchFilters(role_families=["ml_ai"]))
    assert "'ml_ai'" in sql and "IS NULL" not in sql.split("role_family")[-1]


def test_empty_role_families_means_all_roles():
    assert "role_family" not in _sql(SearchFilters(role_families=[]))


def test_duration_and_freshness_filters():
    sql = _sql(SearchFilters(min_duration_months=6, posted_within_days=7))
    assert "duration_months >= 6" in sql
    assert "posted_at >=" in sql


def test_fresher_filter_keeps_internships_that_mention_years():
    sql = _sql(SearchFilters(max_years_experience=0))
    assert "min_years_experience <= 0" in sql
    assert "experience_level = 'internship'" in sql
