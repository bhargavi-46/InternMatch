"""Tags computed from a posting's title and text: role family, internship duration and start month.

Bump TAGS_VERSION whenever these rules or the experience-level rules in filters.py change; the API
re-tags saved jobs on startup.
"""

import re
from typing import Literal

TAGS_VERSION = 3

RoleFamily = Literal["swe", "ml_ai", "data", "devops_cloud", "security", "qa", "other", "non_tech"]
ROLE_FAMILIES: tuple[RoleFamily, ...] = ("swe", "ml_ai", "data", "devops_cloud", "security", "qa", "other", "non_tech")
TECH_FAMILIES: list[RoleFamily] = [f for f in ROLE_FAMILIES if f != "non_tech"]


def _words(*words: str) -> re.Pattern[str]:
    return re.compile(r"\b(" + "|".join(words) + r")\b", re.IGNORECASE)


# Checked in this order; the first match wins.
_FAMILY_RULES: list[tuple[RoleFamily, re.Pattern[str]]] = [
    ("ml_ai", _words(r"machine learning", r"ml", r"ai", r"artificial intelligence", r"deep learning", r"nlp",
                     r"computer vision", r"llms?", r"gen ?ai", r"data scien\w*", r"applied scientist",
                     r"research (engineer|scientist)", r"mlops")),
    ("security", _words(r"security", r"cyber ?security", r"infosec", r"appsec", r"penetration", r"soc analyst",
                        r"vulnerabilit\w*", r"threat", r"malware", r"forensics?")),
    ("devops_cloud", _words(r"devops", r"sre", r"site reliability", r"cloud", r"infrastructure", r"platform engineer\w*",
                            r"systems? engineer", r"network engineer")),
    ("data", _words(r"data engineer\w*", r"data analyst", r"data analytics", r"analytics engineer", r"business intelligence",
                    r"bi (developer|analyst)", r"big data", r"etl")),
    ("qa", _words(r"qa", r"sdet", r"test engineer\w*", r"quality (assurance|engineer\w*)", r"automation tester",
                  r"software test\w*")),
    ("swe", _words(r"software", r"developer", r"sde\s*\d*", r"swe", r"back[- ]?end", r"front[- ]?end", r"full[- ]?stack",
                   r"programmer", r"mobile", r"android", r"ios", r"web", r"engineer(ing)?", r"tech(nical)? intern",
                   r"embedded", r"firmware", r"blockchain", r"game developer")),
]
# Confidently non-technical titles. Only checked when no technical word is present, so "Data Analyst - Finance"
# stays technical but "Analyst - Finance" does not.
_NON_TECH = _words(
    r"marketing", r"sales", r"finance", r"financial", r"accounting", r"accountant", r"legal", r"counsel", r"hr",
    r"human resources", r"people (ops|operations|partner)", r"recruit\w*", r"talent", r"payroll", r"brand",
    r"communications?", r"content", r"copywriter", r"customer (success|support|service|experience)",
    r"account (executive|manager)", r"business development", r"operations", r"procurement", r"supply chain",
    r"logistics", r"social media", r"graphic design\w*", r"tax", r"audit", r"compliance", r"treasury",
    r"controllership", r"administrative", r"office manager", r"partnerships?", r"public relations", r"events?",
)


# Customer-facing roles that borrow engineering words ("Sales Engineer", "Solutions Engineer").
_SALES = _words(r"sales", r"pre-?sales", r"account (executive|manager)", r"business development",
                r"solutions? (engineer|consultant|architect)", r"customer engineer")


def role_family(title: str) -> RoleFamily:
    if _SALES.search(title):
        return "non_tech"
    for family, pattern in _FAMILY_RULES:
        if pattern.search(title):
            return family
    return "non_tech" if _NON_TECH.search(title) else "other"


_NUM = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
        "ten": 10, "eleven": 11, "twelve": 12}
_N = r"(\d{1,2}|" + "|".join(_NUM) + r")"
# "6 months", "6-month", "3-6 months", "three months"; not "3-6 months of experience".
_DURATION = re.compile(
    _N + r"(?:\s*(?:-|–|to)\s*" + _N + r")?[\s-]*months?\b(?!\s+(?:of\s+)?(?:\w+\s+)?experience)",
    re.IGNORECASE,
)
_MONTHS = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
_MONTH = r"(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|june?|july?|aug(?:ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\.?"
_YEAR = r"(?:\s*,?\s*'?(\d{4}|\d{2}))?"
# "January 2027 to May 2027", "(Jan - June 2027)"
_RANGE = re.compile(r"\b" + _MONTH + _YEAR + r"\s*(?:-|–|to|till|until)\s*" + _MONTH + _YEAR + r"\b", re.IGNORECASE)
# "starting in Jan 2027", "available from January", "joining in early February 2027"
_START = re.compile(
    r"\b(?:start\w*|from|join\w*|commenc\w*|beginning|begins?)\s+(?:in\s+|on\s+|from\s+)?(?:early\s+|mid[- ]?\s*)?"
    + _MONTH + _YEAR + r"\b",
    re.IGNORECASE,
)


def _to_int(word: str) -> int:
    return int(word) if word.isdigit() else _NUM[word.lower()]


def _month_index(name: str) -> int:
    return _MONTHS.index(name[:3].lower())


def _year(*values: str | None) -> str:
    for value in values:
        if value:
            return value if len(value) == 4 else f"20{value}"
    return ""


def internship_duration(text: str) -> int | None:
    """Longest internship length in months mentioned in the text (1-12), if any."""
    found = []
    for m in _DURATION.finditer(text):
        found.append(_to_int(m.group(2) or m.group(1)))
    for m in _RANGE.finditer(text):
        found.append((_month_index(m.group(3)) - _month_index(m.group(1))) % 12 + 1)
    found = [n for n in found if 1 <= n <= 12]
    return max(found) if found else None


def internship_start(text: str) -> str | None:
    """Start month such as 'Jan 2027' or 'Jan', if the text states one."""
    m = _RANGE.search(text)
    if m:
        month, year = m.group(1), _year(m.group(2), m.group(4))
    else:
        m = _START.search(text)
        if not m:
            return None
        month, year = m.group(1), _year(m.group(2))
    label = _MONTHS[_month_index(month)].title()
    return f"{label} {year}" if year else label


def job_tags(title: str, description: str, experience_level: str) -> dict:
    tags = {"role_family": role_family(title), "duration_months": None, "start_month": None, "tags_version": TAGS_VERSION}
    if experience_level == "internship":
        text = f"{title}\n{description}"
        tags["duration_months"] = internship_duration(text)
        tags["start_month"] = internship_start(text)
    return tags
