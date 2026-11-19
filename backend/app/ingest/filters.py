import re

from app.ingest.sources import INDIA_PLACE as _INDIA
from app.ingest.sources import Posting

_OPEN_REMOTE = re.compile(r"\b(anywhere|global|worldwide|apac|asia)\b", re.IGNORECASE)
_INTERN = re.compile(r"\b(intern|interns|internship|co-?op|apprentice|apprenticeship|trainee)\b", re.IGNORECASE)
_ENTRY = re.compile(
    r"\b(new grad|new graduate|graduate|graduates|entry[- ]level|fresher|freshers|early career|university|campus|"
    r"junior|sde[- ]?(1|i)|associate (software|engineer|tse|data|product manager)|apm)\b",
    re.IGNORECASE,
)
# Titles that always need experience, even next to an entry-level word ("Senior Associate Software Engineer").
_SENIOR = re.compile(
    r"\b(senior|sr|lead|staff|principal|director|head|vp|avp|svp|chief|architect|expert|deputy|partner|"
    r"president|ii|iii|iv|vi|l[2-9])\b|\b[2-9]\s*$",
    re.IGNORECASE,
)
# Manager-type titles need experience unless the title also says entry level ("Associate Product Manager").
_MANAGER = re.compile(r"\b(manager|managers|mgr)\b", re.IGNORECASE)
_LEVEL_ONE = re.compile(r"\b(i|1)\s*$", re.IGNORECASE)
# "3+ years of experience", "2-4 years experience", "0 to 1 years of relevant experience"
_YEARS = re.compile(
    r"\b(\d{1,2})\s*(?:\+|(?:-|–|to)\s*\d{1,2})?\s*\+?\s*(?:years?|yrs?)(?:\s+\w+){0,4}?\s+experience"
    # "minimum 3 years", "at least 2 yrs", "experience of 4+ years", "experience: 3-5 years"
    r"|(?:minimum|min\.?|at least|atleast|experience\s*(?:of|:|-|–)?)\s*(?:of\s+)?(\d{1,2})\s*\+?\s*"
    r"(?:(?:-|–|to)\s*\d{1,2}\s*)?(?:years?|yrs?)\b",
    re.IGNORECASE,
)
# Years stated in the title itself: "ASIC Engineer - 5 years to 13Years", "Analyst (3+ yrs)"
_TITLE_YEARS = re.compile(r"\b(\d{1,2})\s*\+?\s*(?:(?:-|–|to)\s*\d{1,2}\s*)?(?:years?|yrs?)\b", re.IGNORECASE)


def min_years_experience(description: str, title: str = "") -> int | None:
    """Fewest years of experience asked for. Years in the title win over the description, which may also mention
    smaller numbers for single skills ("1+ years with Kubernetes")."""
    if m := _TITLE_YEARS.search(title):
        return int(m.group(1))
    years = [int(m.group(1) or m.group(2)) for m in _YEARS.finditer(description)]
    return min(years) if years else None


def is_relevant_location(posting: Posting) -> bool:
    """Keep jobs based in India, or remote jobs not restricted to another country."""
    if _INDIA.search(posting.location):
        return True
    if not posting.is_remote:
        return False
    rest = re.sub(r"remote", "", posting.location, flags=re.IGNORECASE).strip(" -,;()/|")
    return not rest or bool(_OPEN_REMOTE.search(rest))


def experience_level(posting: Posting) -> str:
    return classify_level(posting.title, posting.description, posting.employment_type)


def classify_level(title: str, description: str, employment_type: str | None) -> str:
    """internship, entry_level (open to freshers) or other. A job counts as entry level only on a clear signal."""
    title = title.replace("_", " ")  # "IN_RBIN_Senior Engineer" is still a senior title
    if _INTERN.search(title) or (employment_type or "").lower() in {"intern", "internship"}:
        return "internship"
    years = min_years_experience(description, title)
    # Stated experience beats a junior-sounding title ("Associate TSE, 4+ years").
    if years is not None and years >= 2:
        return "other"
    if _SENIOR.search(title):
        return "other"
    if _ENTRY.search(title):
        return "entry_level"
    if _MANAGER.search(title):
        return "other"
    if employment_type == "entry_level" or (years is not None and years <= 1) or _LEVEL_ONE.search(title):
        return "entry_level"
    return "other"
