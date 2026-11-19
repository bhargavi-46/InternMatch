import pytest

from app.ingest.filters import experience_level, is_relevant_location, min_years_experience
from app.ingest.sources import Posting, html_to_text


def make(title="Engineer", location="Bengaluru, India", is_remote=False, description="", employment_type=None):
    return Posting(
        source="test", external_id="1", company="Acme", title=title, location=location, is_remote=is_remote,
        employment_type=employment_type, description=description, url="https://example.com", posted_at=None,
    )


@pytest.mark.parametrize(
    ("location", "is_remote", "expected"),
    [
        ("Bengaluru, India", False, True),
        ("Gurgaon", False, True),
        ("Indianapolis, IN", False, False),
        ("San Francisco, CA", False, False),
        ("Remote", True, True),
        ("Remote - APAC", True, True),
        ("Remote - US", True, False),
    ],
)
def test_is_relevant_location(location, is_remote, expected):
    assert is_relevant_location(make(location=location, is_remote=is_remote)) is expected


@pytest.mark.parametrize(
    ("title", "description", "employment_type", "expected"),
    [
        ("Software Engineering Intern", "", None, "internship"),
        ("Machine Learning Engineer", "", "Intern", "internship"),
        ("Internal Audit Manager", "", None, "other"),
        ("SDE-1, Backend", "", None, "entry_level"),
        ("Associate TSE", "We need 4+ years of experience in support.", None, "other"),
        ("Software Engineer", "0-1 years of experience with Python.", None, "entry_level"),
        ("Senior Software Engineer", "", None, "other"),
        ("Product Manager I", "", None, "other"),
        ("Sales Manager - I", "", None, "other"),
        ("Associate Product Manager", "", None, "entry_level"),
        ("IN_RBIN_Senior Engineer/Assistant Manager_Front Line Manager", "", "entry_level", "other"),
        ("Customer Success Engineer - II", "1+ years of experience", None, "other"),
        ("Captain 2", "", None, "other"),
        ("AI/ML Expert", "", None, "other"),
        ("Senior Associate Software Engineer", "", None, "other"),
        ("SDE I", "", None, "entry_level"),
        ("Project Management Associate", "0-1 years of experience", None, "entry_level"),
        ("ASIC Verification Engineer - 5 years to 13Years", "1+ years of experience with UVM", None, "other"),
        ("Research Engineer", "Experience : At least 3 years of relevant work", "entry_level", "other"),
        ("Data Analyst", "", None, "other"),  # no signal either way: not shown as entry level
    ],
)
def test_experience_level(title, description, employment_type, expected):
    assert experience_level(make(title=title, description=description, employment_type=employment_type)) == expected


@pytest.mark.parametrize(
    ("description", "expected"),
    [
        ("Requires 3+ years of experience.", 3),
        ("2-4 years of relevant industry experience", 2),
        ("0 to 1 years experience; 5 years of experience preferred", 0),
        ("No experience needed.", None),
        ("Experience: 1 - 2 years as content creator", 1),
        ("Minimum 4 yrs in backend development", 4),
    ],
)
def test_min_years_experience(description, expected):
    assert min_years_experience(description) == expected


def test_years_in_the_title_win_over_the_description():
    assert min_years_experience("1+ years of experience with Python", "Analyst - 3+ yrs") == 3


def test_html_to_text_handles_double_escaped_html():
    assert html_to_text("&lt;p&gt;We&amp;#39;re hiring&lt;/p&gt;") == "We're hiring"
