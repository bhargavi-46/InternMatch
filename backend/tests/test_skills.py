from app.profile import StudentProfile
from app.skills import extract_skills


def test_finds_common_skills_with_aliases():
    text = "We use Python, PyTorch and sklearn; services run on k8s with Postgres and GitHub Actions."
    assert {"Python", "PyTorch", "scikit-learn", "Kubernetes", "PostgreSQL", "CI/CD"} <= extract_skills(text)


def test_does_not_confuse_everyday_words():
    text = "Spring 2027 internship. Express your interest and go to our page. Excellent node in the graph."
    assert extract_skills(text) & {"Spring", "Express", "Go", "Excel", "Node.js"} == set()


def test_java_is_not_javascript():
    assert extract_skills("JavaScript developer") == {"JavaScript"}


def test_single_letter_languages_need_list_context():
    assert {"C", "C++", "R"} <= extract_skills("Languages: C, C++, R and Python")
    assert "C" not in extract_skills("Grade C student")


def test_profile_skill_set_handles_last_item():
    profile = StudentProfile(summary="x", skills=["Python", "C"], target_roles=["SDE Intern"])
    assert profile.skill_set() == {"Python", "C"}


def test_profile_keyword_query_is_or_of_phrases():
    profile = StudentProfile(summary="x", skills=['Node "js"'], target_roles=["ML Intern"])
    assert profile.keyword_query() == '"ML Intern" or "Node js"'
