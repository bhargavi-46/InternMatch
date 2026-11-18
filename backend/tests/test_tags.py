import pytest

from app.ingest.tags import internship_duration, internship_start, job_tags, role_family


@pytest.mark.parametrize(
    ("title", "family"),
    [
        ("Software Engineer, Intern", "swe"),
        ("Associate Software Development Engineer (SDE) Intern", "swe"),
        ("Backend Interns", "swe"),
        ("AI Researcher Intern", "ml_ai"),
        ("Machine Learning Engineer", "ml_ai"),
        ("Data Scientist - NLP", "ml_ai"),
        ("Data Engineer", "data"),
        ("Data Analyst - Finance", "data"),
        ("DevOps Engineer", "devops_cloud"),
        ("Site Reliability Engineer II", "devops_cloud"),
        ("Security Engineer Intern", "security"),
        ("Associate Software Test Engineer (Playwright)", "qa"),
        ("Marketing internship (brand & communication)", "non_tech"),
        ("Industrial Trainee - Finance & Accounting", "non_tech"),
        ("Intern - Talent Acquisition", "non_tech"),
        ("Social Media Intern", "non_tech"),
        ("People Operations Intern", "non_tech"),
        ("Regional Sales Engineer - Delhi", "non_tech"),
        ("Solutions Engineer, India", "non_tech"),
        ("Engineer II - Vulnerability Detection", "security"),
        ("Product Management Intern", "other"),
        ("ENG Project/ Program - Intern", "other"),
    ],
)
def test_role_family(title, family):
    assert role_family(title) == family


@pytest.mark.parametrize(
    ("text", "months"),
    [
        ("This is a 6-month full-time onsite internship (Jan - June 2027).", 6),
        ("Duration: 3 Months", 3),
        ("Duration 6-month engagement. Opportunity for conversion.", 6),
        ("Available from January 2027 to May 2027 in Bangalore", 5),
        ("for the full 2 months (we are willing to extend the internship tenure to 6 months)", 6),
        ("a six month internship", 6),
        ("3-6 months of experience in social media management", None),
        ("Assist with month-end closing processes", None),
        ("deploy models within moments, not months", None),
    ],
)
def test_internship_duration(text, months):
    assert internship_duration(text) == months


@pytest.mark.parametrize(
    ("text", "start"),
    [
        ("This is a 6-month full-time onsite internship (Jan - June 2027).", "Jan 2027"),
        ("Available from January 2027 to May 2027", "Jan 2027"),
        ("a 6-month Apprenticeship Intern Program, starting in Jan 2027 and run in", "Jan 2027"),
        ("Interns joining in early February", "Feb"),
        ("Assist with month-end closing and the decision process", None),
        ("Marketing to new users", None),
    ],
)
def test_internship_start(text, start):
    assert internship_start(text) == start


def test_duration_and_start_only_for_internships():
    text = "This is a 6-month role starting in Jan 2027."
    assert job_tags("Software Engineer", text, "entry_level")["duration_months"] is None
    tags = job_tags("Software Engineer Intern", text, "internship")
    assert (tags["role_family"], tags["duration_months"], tags["start_month"]) == ("swe", 6, "Jan 2027")
