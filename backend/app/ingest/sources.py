import asyncio
import html
import re
import weakref
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

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


INDIA_PLACE = re.compile(
    r"\b(india|bengaluru|bangalore|mumbai|delhi|new delhi|gurugram|gurgaon|noida|hyderabad|pune|"
    r"chennai|kolkata|ahmedabad|jaipur|kochi|chandigarh)\b",
    re.IGNORECASE,
)
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


WORKDAY_MAX_POSTINGS = 400  # per company; big employers list thousands of India roles
_WORKDAY_AGO = re.compile(r"(\d+)\+? days? ago", re.IGNORECASE)


def _workday_values(facets: list[dict]):
    """Yield (facet parameter, value) for every leaf value; Workday nests facet groups."""
    for facet in facets:
        for value in facet.get("values", []):
            if "values" in value:
                yield from _workday_values([value])
            else:
                yield facet["facetParameter"], value


_INDIA_WORD = re.compile(r"\bindia\b", re.IGNORECASE)


def _workday_india_facet(facets: list[dict]) -> tuple[str, list[str]] | None:
    """The facet filter that limits a Workday site to India: a country value if the site has one,
    otherwise every location value that names India ("Bangalore, India", "India, Pune")."""
    values = list(_workday_values(facets))
    for param, value in values:
        if value.get("descriptor") == "India":
            return param, [value["id"]]
    by_param: dict[str, list[str]] = {}
    for param, value in values:
        if _INDIA_WORD.search(value.get("descriptor") or ""):
            by_param.setdefault(param, []).append(value["id"])
    if not by_param:
        return None
    param = max(by_param, key=lambda k: len(by_param[k]))
    return param, by_param[param]


def _workday_location(location: str) -> str:
    if _INDIA_WORD.search(location):
        return location
    if INDIA_PLACE.search(location):
        return f"{location}, India"  # "Mumbai, Nirlon Knowledge Park"
    # The site was filtered to India, so a job whose main location is elsewhere also has an India one.
    return f"{location} (also India)" if location else "India"


def _workday_posted(info: dict) -> datetime | None:
    if info.get("startDate"):
        return datetime.fromisoformat(info["startDate"]).replace(tzinfo=timezone.utc)
    text = info.get("postedOn") or ""
    if "today" in text.lower():
        return datetime.now(timezone.utc)
    if "yesterday" in text.lower():
        return datetime.now(timezone.utc) - timedelta(days=1)
    m = _WORKDAY_AGO.search(text)
    return datetime.now(timezone.utc) - timedelta(days=int(m.group(1))) if m else None


# Workday rate-limits by IP across all its customers, so every Workday request in a run shares one limit,
# and a 429 pauses all of them (not just the request that got it) until Workday's wait time has passed.
_workday_limits: "weakref.WeakKeyDictionary[httpx.AsyncClient, asyncio.Semaphore]" = weakref.WeakKeyDictionary()
_workday_pause_until: "weakref.WeakKeyDictionary[httpx.AsyncClient, float]" = weakref.WeakKeyDictionary()
WORKDAY_MAX_WAIT = 120  # seconds; ignore longer Retry-After values and give up on that board instead
_SENIOR_TITLE = re.compile(
    r"\b(senior|sr|lead|staff|principal|director|head|vp|vice president|architect|manager)\b", re.IGNORECASE
)


def _retry_delay(resp: httpx.Response | None, attempt: int) -> float:
    """Seconds to wait before retrying: Workday's Retry-After when it sends one, else 5, 10, 20, 40 seconds."""
    header = resp.headers.get("retry-after", "") if resp is not None else ""
    if header.strip().isdigit():
        return min(float(header), WORKDAY_MAX_WAIT)
    return 5.0 * 2**attempt


async def _workday_send(client: httpx.AsyncClient, method: str, url: str, **kwargs) -> dict:
    limit = _workday_limits.setdefault(client, asyncio.Semaphore(2))
    loop = asyncio.get_running_loop()
    for attempt in range(5):
        last = attempt == 4
        resp = None
        try:
            async with limit:
                while (wait := _workday_pause_until.get(client, 0.0) - loop.time()) > 0:
                    await asyncio.sleep(wait)
                # Without this header Workday answers 429 to every request, as if rate-limited.
                resp = await client.request(method, url, headers={"Accept": "application/json"}, **kwargs)
        except httpx.TransportError:  # Workday sometimes drops busy connections
            if last:
                raise
        else:
            if resp.status_code != 429 or last:
                resp.raise_for_status()
                return resp.json()
        delay = _retry_delay(resp, attempt)
        if resp is not None:  # rate-limited: hold back every Workday request, not just this one
            _workday_pause_until[client] = max(_workday_pause_until.get(client, 0.0), loop.time() + delay)
        await asyncio.sleep(delay)
    raise AssertionError("unreachable")


async def fetch_workday(client: httpx.AsyncClient, slug: str, company: str) -> list[Posting]:
    """India postings from a Workday careers site's public JSON API (no key needed).

    `slug` is "<tenant>.<wd host>/<site>", e.g. "nvidia.wd5/NVIDIAExternalCareerSite".
    Clearly senior titles are skipped before fetching details, to keep the request count (and 429s) down.
    """
    host, site = slug.split("/", 1)
    tenant = host.split(".", 1)[0]
    root = f"https://{host}.myworkdayjobs.com"
    base = f"{root}/wday/cxs/{tenant}/{site}"

    async def page(offset: int, facets: dict) -> dict:
        body = {"appliedFacets": facets, "limit": 20, "offset": offset, "searchText": ""}
        return await _workday_send(client, "POST", f"{base}/jobs", json=body)

    first = await page(0, {})
    india = _workday_india_facet(first.get("facets", []))
    if india is None:
        return []  # no India filter on this site, so no India jobs to list
    facets = {india[0]: india[1]}
    data = await page(0, facets)
    summaries, total = data["jobPostings"], min(data["total"], WORKDAY_MAX_POSTINGS)
    while len(summaries) < total:
        more = (await page(len(summaries), facets))["jobPostings"]
        if not more:
            break
        summaries += more
    summaries = [s for s in summaries if s.get("externalPath") and not _SENIOR_TITLE.search(s["title"])]

    async def detail(summary: dict) -> Posting:
        try:
            info = (await _workday_send(client, "GET", f"{base}{summary['externalPath']}"))["jobPostingInfo"]
        except (httpx.HTTPError, KeyError, ValueError):
            # Keep the job (title, location, link) even if its description could not be loaded.
            info = {"title": summary["title"], "location": summary.get("locationsText"), "postedOn": summary.get("postedOn")}
        location = info.get("location") or summary.get("locationsText") or ""
        return Posting(
            source="workday",
            external_id=f"{tenant}:{summary['externalPath'].rsplit('_', 1)[-1]}",
            company=company,
            title=info.get("title") or summary["title"],
            location=_workday_location(location),
            is_remote="remote" in location.lower() or "virtual" in location.lower(),
            employment_type=None,
            description=html_to_text(info.get("jobDescription")),
            url=info.get("externalUrl") or f"{root}/{site}{summary['externalPath']}",
            posted_at=_workday_posted(info),
        )

    return list(await asyncio.gather(*(detail(s) for s in summaries)))

FETCHERS = {
    "greenhouse": fetch_greenhouse,
    "lever": fetch_lever,
    "ashby": fetch_ashby,
    "smartrecruiters": fetch_smartrecruiters,
    "workday": fetch_workday,
}
