import html
import re
from dataclasses import dataclass
from datetime import datetime, timezone

import httpx


@dataclass
class Posting:
    source: str
    external_id: str
    company: str
    title: str
    location: str
    is_remote: bool
    employment_type: str | None
    description: str
    url: str
    posted_at: datetime | None


_TAG = re.compile(r"<[^>]+>")
_SPACE = re.compile(r"\s+")


def html_to_text(raw: str | None) -> str:
    # Greenhouse double-escapes its HTML, so unescape once before and once after stripping tags.
    text = html.unescape(_TAG.sub(" ", html.unescape(raw or "")))
    return _SPACE.sub(" ", text).strip()


def _parse_iso(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None


async def fetch_greenhouse(client: httpx.AsyncClient, slug: str, company: str) -> list[Posting]:
    resp = await client.get(
        f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs", params={"content": "true"}
    )
    resp.raise_for_status()
    postings = []
    for job in resp.json()["jobs"]:
        location = (job.get("location") or {}).get("name") or ""
        postings.append(
            Posting(
                source="greenhouse",
                external_id=str(job["id"]),
                company=company,
                title=job["title"],
                location=location,
                is_remote="remote" in location.lower(),
                employment_type=None,
                description=html_to_text(job.get("content")),
                url=job["absolute_url"],
                posted_at=_parse_iso(job.get("first_published") or job.get("updated_at")),
            )
        )
    return postings


async def fetch_lever(client: httpx.AsyncClient, slug: str, company: str) -> list[Posting]:
    resp = await client.get(f"https://api.lever.co/v0/postings/{slug}", params={"mode": "json"})
    resp.raise_for_status()
    postings = []
    for job in resp.json():
        categories = job.get("categories") or {}
        location = categories.get("location") or ", ".join(categories.get("allLocations") or [])
        sections = [job.get("descriptionPlain") or ""]
        sections += [f"{item['text']}: {html_to_text(item['content'])}" for item in job.get("lists") or []]
        sections.append(job.get("additionalPlain") or "")
        created_ms = job.get("createdAt")
        postings.append(
            Posting(
                source="lever",
                external_id=job["id"],
                company=company,
                title=job["text"],
                location=location,
                is_remote=job.get("workplaceType") == "remote" or "remote" in location.lower(),
                employment_type=categories.get("commitment"),
                description=" ".join(s for s in sections if s).strip(),
                url=job["hostedUrl"],
                posted_at=datetime.fromtimestamp(created_ms / 1000, tz=timezone.utc) if created_ms else None,
            )
        )
    return postings


async def fetch_ashby(client: httpx.AsyncClient, slug: str, company: str) -> list[Posting]:
    resp = await client.get(f"https://api.ashbyhq.com/posting-api/job-board/{slug}")
    resp.raise_for_status()
    postings = []
    for job in resp.json()["jobs"]:
        if not job.get("isListed", True):
            continue
        locations = [job.get("location") or ""]
        locations += [s.get("location") or "" for s in job.get("secondaryLocations") or []]
        postings.append(
            Posting(
                source="ashby",
                external_id=job["id"],
                company=company,
                title=job["title"],
                location="; ".join(loc for loc in locations if loc),
                is_remote=bool(job.get("isRemote")) or job.get("workplaceType") == "Remote",
                employment_type=job.get("employmentType"),
                description=job.get("descriptionPlain") or html_to_text(job.get("descriptionHtml")),
                url=job["jobUrl"],
                posted_at=_parse_iso(job.get("publishedAt")),
            )
        )
    return postings


ADZUNA_QUERIES: list[dict[str, str]] = [
    {"what_or": "intern internship trainee fresher", "category": "it-jobs"},
    {"what": "software engineer intern"},
    {"what": "machine learning intern"},
    {"what": "data science intern"},
    {"what": "software developer fresher"},
]
_REMOTE = re.compile(r"\b(remote|work from home|wfh)\b", re.IGNORECASE)


def _adzuna_posting(job: dict) -> Posting:
    title = html_to_text(job["title"])
    description = html_to_text(job.get("description"))
    location = (job.get("location") or {}).get("display_name") or ""
    if "india" not in location.lower():
        location = f"{location}, India" if location else "India"
    return Posting(
        source="adzuna",
        external_id=str(job["id"]),
        company=((job.get("company") or {}).get("display_name") or "Unknown")[:100],
        title=title,
        location=location,
        is_remote=bool(_REMOTE.search(f"{title} {location}")),
        employment_type=job.get("contract_time"),
        description=description,
        url=job["redirect_url"],
        posted_at=_parse_iso(job.get("created")),
    )


async def fetch_adzuna(
    client: httpx.AsyncClient, app_id: str, app_key: str, pages_per_query: int = 3
) -> list[Posting]:
    """Search Adzuna India. Note: Adzuna returns a description snippet, not the full posting."""
    found: dict[str, Posting] = {}
    for query in ADZUNA_QUERIES:
        for page in range(1, pages_per_query + 1):
            # Sequential on purpose: the free tier is rate limited.
            resp = await client.get(
                f"https://api.adzuna.com/v1/api/jobs/in/search/{page}",
                params={
                    "app_id": app_id,
                    "app_key": app_key,
                    "results_per_page": 50,
                    "max_days_old": 30,
                    "sort_by": "date",
                    **query,
                },
            )
            resp.raise_for_status()
            results = resp.json()["results"]
            for job in results:
                posting = _adzuna_posting(job)
                found[posting.external_id] = posting
            if len(results) < 50:
                break
    return list(found.values())


FETCHERS = {
    "greenhouse": fetch_greenhouse,
    "lever": fetch_lever,
    "ashby": fetch_ashby,
}
