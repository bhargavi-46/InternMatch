import asyncio

import httpx

from app.ingest.sources import ADZUNA_QUERIES, fetch_adzuna


def adzuna_job(job_id, title="<strong>Software</strong> Intern", location="Bangalore, Karnataka"):
    return {
        "id": job_id,
        "title": title,
        "description": "Work on &amp; ship <b>Python</b> services.",
        "location": {"display_name": location},
        "company": {"display_name": "Acme Labs"},
        "contract_time": "full_time",
        "redirect_url": f"https://www.adzuna.in/details/{job_id}",
        "created": "2026-11-10T08:30:00Z",
    }


def run_fetch(handler):
    async def go():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            return await fetch_adzuna(client, "id", "key", pages_per_query=3)

    return asyncio.run(go())


def test_maps_fields_and_cleans_html():
    postings = run_fetch(lambda request: httpx.Response(200, json={"results": [adzuna_job(1)]}))

    assert len(postings) == 1
    p = postings[0]
    assert p.source == "adzuna"
    assert p.external_id == "1"
    assert p.title == "Software Intern"
    assert p.description == "Work on & ship Python services."
    assert p.company == "Acme Labs"
    assert p.location == "Bangalore, Karnataka, India"
    assert p.posted_at.year == 2026


def test_paginates_until_short_page_and_dedupes_across_queries():
    pages_requested = []

    def handler(request):
        page = int(request.url.path.rsplit("/", 1)[-1])
        pages_requested.append(page)
        if page == 1:
            return httpx.Response(200, json={"results": [adzuna_job(i) for i in range(50)]})
        return httpx.Response(200, json={"results": [adzuna_job(999)]})

    postings = run_fetch(handler)

    # Every query reads a full page 1, then a short page 2, and stops.
    assert pages_requested == [1, 2] * len(ADZUNA_QUERIES)
    # The same 51 ids come back for every query; each is kept once.
    assert len(postings) == 51


def test_location_without_india_is_marked_india():
    postings = run_fetch(lambda r: httpx.Response(200, json={"results": [adzuna_job(7, location="Karnataka")]}))
    assert postings[0].location == "Karnataka, India"


def test_sends_credentials_and_query():
    seen = []

    def handler(request):
        seen.append(dict(request.url.params))
        return httpx.Response(200, json={"results": []})

    run_fetch(handler)

    assert seen[0]["app_id"] == "id"
    assert seen[0]["app_key"] == "key"
    assert seen[0]["what_or"] == ADZUNA_QUERIES[0]["what_or"]
