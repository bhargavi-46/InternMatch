import asyncio
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


# SmartRecruiters tags each posting with a level; pass the student-level ones on to the classifier.
_SR_LEVELS = {"internship": "internship", "entry_level": "entry_level"}
_SR_SECTIONS = ("jobDescription", "qualifications", "additionalInformation")


def _smartrecruiters_posting(job: dict, company: str) -> Posting:
    """Build a posting from a SmartRecruiters detail response (or a list summary, which has no jobAd)."""
    location = job.get("location") or {}
    sections = (job.get("jobAd") or {}).get("sections") or {}
    level = (job.get("experienceLevel") or {}).get("id")
    employment = job.get("typeOfEmployment") or {}
    if employment.get("id") in {"intern", "internship"}:
        level = "internship"
    return Posting(
        source="smartrecruiters",
        external_id=str(job["id"]),
        company=company,
        title=job["name"],
        # Only India postings are requested, so a missing full location is still in India.
        location=location.get("fullLocation") or ", ".join(x for x in (location.get("city"), "India") if x),
        is_remote=bool(location.get("remote")),
        employment_type=_SR_LEVELS.get(level) or employment.get("label"),
        description=" ".join(html_to_text((sections.get(k) or {}).get("text")) for k in _SR_SECTIONS).strip(),
        url=job.get("postingUrl") or f"https://jobs.smartrecruiters.com/{company}/{job['id']}",
        posted_at=_parse_iso(job.get("releasedDate")),
    )


async def fetch_smartrecruiters(client: httpx.AsyncClient, slug: str, company: str) -> list[Posting]:
    """India postings from the public SmartRecruiters Posting API (no key needed).

    The list endpoint has no description, so each posting's details are fetched too.
    """
    base = f"https://api.smartrecruiters.com/v1/companies/{slug}/postings"
    summaries: list[dict] = []
    while True:
        resp = await client.get(base, params={"country": "in", "limit": 100, "offset": len(summaries)})
        resp.raise_for_status()
        data = resp.json()
        summaries += data["content"]
        if not data["content"] or len(summaries) >= data["totalFound"]:
            break

    limit = asyncio.Semaphore(4)

    async def detail(summary: dict) -> Posting:
        async with limit:
            try:
                resp = await client.get(f"{base}/{summary['id']}")
                resp.raise_for_status()
                return _smartrecruiters_posting(resp.json(), company)
            except httpx.HTTPError:
                # Keep the job (title, level, location) even if its description could not be loaded.
                return _smartrecruiters_posting(summary, company)

    return list(await asyncio.gather(*(detail(s) for s in summaries)))


FETCHERS = {
    "greenhouse": fetch_greenhouse,
    "lever": fetch_lever,
    "ashby": fetch_ashby,
    "smartrecruiters": fetch_smartrecruiters,
}
