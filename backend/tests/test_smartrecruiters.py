import asyncio

import httpx

from app.ingest.filters import experience_level
from app.ingest.sources import fetch_smartrecruiters


def summary(job_id, name="Software Engineer", level="entry_level", employment="permanent"):
    return {
        "id": str(job_id),
        "name": name,
        "releasedDate": "2026-11-10T08:30:00.000Z",
        "location": {"city": "Bengaluru", "country": "in", "remote": False, "fullLocation": "Bengaluru, KA, India"},
        "experienceLevel": {"id": level},
        "typeOfEmployment": {"id": employment, "label": employment.title()},
    }


def detail(job_summary):
    return {
        **job_summary,
        "postingUrl": f"https://jobs.smartrecruiters.com/ACME/{job_summary['id']}-software-engineer",
        "jobAd": {
            "sections": {
                "companyDescription": {"text": "<p>About Acme</p>"},
                "jobDescription": {"text": "<p>Build <b>Python</b> services &amp; APIs.</p>"},
                "qualifications": {"text": "<ul><li>0-1 years of experience</li></ul>"},
                "additionalInformation": {"text": ""},
            }
        },
    }


def run_fetch(handler):
    async def go():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            return await fetch_smartrecruiters(client, "Acme", "Acme")

    return asyncio.run(go())


def list_and_detail(summaries, details=None):
    details = details or {}
    by_id = {s["id"]: s for s in summaries}

    def handler(request):
        if request.url.path.endswith("/postings"):
            offset = int(request.url.params["offset"])
            page = summaries[offset : offset + 100]
            return httpx.Response(200, json={"totalFound": len(summaries), "content": page})
        job_id = request.url.path.rsplit("/", 1)[-1]
        return details.get(job_id) or httpx.Response(200, json=detail(by_id[job_id]))

    return handler


def test_maps_detail_fields_and_cleans_html():
    postings = run_fetch(list_and_detail([summary(1)]))

    assert len(postings) == 1
    p = postings[0]
    assert p.source == "smartrecruiters"
    assert p.external_id == "1"
    assert p.location == "Bengaluru, KA, India"
    assert p.url == "https://jobs.smartrecruiters.com/ACME/1-software-engineer"
    # Company boilerplate is left out; the role sections are kept as plain text.
    assert p.description == "Build Python services & APIs. 0-1 years of experience"
    assert p.posted_at.year == 2026


def test_requests_india_only_and_pages_through_all_postings():
    seen = []
    summaries = [summary(i) for i in range(150)]
    handler = list_and_detail(summaries)

    def recording(request):
        if request.url.path.endswith("/postings"):
            seen.append(dict(request.url.params))
        return handler(request)

    postings = run_fetch(recording)

    assert [s["offset"] for s in seen] == ["0", "100"]
    assert all(s["country"] == "in" for s in seen)
    assert len(postings) == 150


def test_failed_detail_keeps_the_job_without_description():
    handler = list_and_detail([summary(1), summary(2)], details={"2": httpx.Response(500)})

    postings = {p.external_id: p for p in run_fetch(handler)}

    assert postings["1"].description
    assert postings["2"].description == ""
    assert postings["2"].title == "Software Engineer"


def test_levels_come_from_smartrecruiters_tags():
    postings = run_fetch(
        list_and_detail(
            [
                summary(1, name="Analyst", level="internship"),
                summary(2, name="Analyst", level="mid_senior_level", employment="intern"),
                summary(3, name="Analyst", level="entry_level"),
                summary(4, name="Senior Analyst", level="mid_senior_level"),
            ]
        )
    )
    levels = {p.external_id: experience_level(p) for p in postings}

    assert levels == {"1": "internship", "2": "internship", "3": "entry_level", "4": "other"}
