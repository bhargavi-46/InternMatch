import re

from app.ingest.sources import Posting

_INDIA = re.compile(
    r"\b(india|bengaluru|bangalore|mumbai|delhi|new delhi|gurugram|gurgaon|noida|hyderabad|pune|"
    r"chennai|kolkata|ahmedabad|jaipur|kochi|chandigarh)\b",
    re.IGNORECASE,
)
_OPEN_REMOTE = re.compile(r"\b(anywhere|global|worldwide|apac|asia)\b", re.IGNORECASE)
_INTERN = re.compile(r"\b(intern|interns|internship|co-?op|apprentice|apprenticeship|trainee)\b", re.IGNORECASE)
_ENTRY = re.compile(
    r"\b(new grad|new graduate|graduate|entry[- ]level|fresher|freshers|early career|university|campus|junior|"
    r"sde[- ]?(1|i)|associate (software|engineer|tse))\b",
    re.IGNORECASE,
)
_SENIOR = re.compile(r"\b(senior|sr|lead|staff|principal|director|head|vp|architect)\b", re.IGNORECASE)
_LEVEL_ONE = re.compile(r"\b(i|1)\s*$", re.IGNORECASE)
# "3+ years of experience", "2-4 years experience", "0 to 1 years of relevant experience"
_YEARS = re.compile(
    r"\b(\d{1,2})\s*(?:\+|(?:-|–|to)\s*\d{1,2})?\s*\+?\s*years?(?:\s+\w+){0,4}?\s+experience",
    re.IGNORECASE,
)


def min_years_experience(description: str) -> int | None:
    years = [int(m.group(1)) for m in _YEARS.finditer(description)]
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
    if _INTERN.search(posting.title) or (posting.employment_type or "").lower() in {"intern", "internship"}:
        return "internship"
    years = min_years_experience(posting.description)
    # Stated experience beats a junior-sounding title ("Associate TSE, 4+ years").
    if years is not None and years >= 2:
        return "other"
    if _ENTRY.search(posting.title) or posting.employment_type == "entry_level":
        return "entry_level"
    if _SENIOR.search(posting.title):
        return "other"
    if (years is not None and years <= 1) or _LEVEL_ONE.search(posting.title):
        return "entry_level"
    return "other"
