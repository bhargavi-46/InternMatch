import asyncio
import json

import httpx

from app.ingest import sources
from app.ingest.sources import _workday_india_facet, fetch_workday

BASE = "https://acme.wd5.myworkdayjobs.com/wday/cxs/acme/External"
FACETS = [
    {"facetParameter": "jobFamilyGroup", "values": [{"descriptor": "Engineering", "id": "eng", "count": 9}]},
    {
        "facetParameter": "locationMainGroup",
        "values": [
            {
                "facetParameter": "locationHierarchy1",
                "descriptor": "Locations",
                "values": [{"descriptor": "India", "id": "in", "count": 25}, {"descriptor": "Japan", "id": "jp"}],
            }
        ],
    },
]
TITLES = [f"Software Engineer Intern {i}" for i in range(22)] + ["Senior Staff Engineer", "Engineering Manager"]


def summary(i, title):
    return {"title": title, "externalPath": f"/job/India-Pune/Job-{i}_JR{i}", "locationsText": "India, Pune",
            "postedOn": "Posted 3 Days Ago"}


def test_india_facet_found_in_nested_groups():
    assert _workday_india_facet(FACETS) == ("locationHierarchy1", ["in"])


def test_india_facet_falls_back_to_city_values():
    facets = [{"facetParameter": "locations", "values": [
        {"descriptor": "Bangalore, Karnataka, India", "id": "blr"}, {"descriptor": "Indiana, United States", "id": "us"},
        {"descriptor": "Pune, India", "id": "pune"},
    ]}]
    assert _workday_india_facet(facets) == ("locations", ["blr", "pune"])


def test_fetch_workday_filters_to_india_pages_and_skips_senior_titles(monkeypatch):
    monkeypatch.setattr(sources, "_retry_delay", lambda resp, attempt: 0.0)
    calls = {"rate_limited": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["accept"] == "application/json"
        if request.method == "POST":
            body = json.loads(request.content)
            if not body["appliedFacets"]:
                return httpx.Response(200, json={"total": 500, "facets": FACETS, "jobPostings": []})
            assert body["appliedFacets"] == {"locationHierarchy1": ["in"]}
            page = [summary(i, t) for i, t in enumerate(TITLES)][body["offset"]: body["offset"] + 20]
            return httpx.Response(200, json={"total": len(TITLES), "jobPostings": page})
        if request.url.path.endswith("JR0") and calls["rate_limited"] == 0:
            calls["rate_limited"] += 1
            return httpx.Response(429)
        i = request.url.path.rsplit("JR", 1)[1]
        return httpx.Response(200, json={"jobPostingInfo": {
            "title": TITLES[int(i)], "location": "India, Pune", "startDate": "2026-11-15",
            "jobDescription": "<p>Build <b>Python</b> services. 6 month internship.</p>",
            "externalUrl": f"https://acme.wd5.myworkdayjobs.com/External/job/India-Pune/Job-{i}_JR{i}",
        }})

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            return await fetch_workday(client, "acme.wd5/External", "Acme")

    postings = asyncio.run(run())
    assert len(postings) == 22  # both senior titles skipped
    assert calls["rate_limited"] == 1  # the 429 was retried
    first = postings[0]
    assert first.source == "workday" and first.external_id == "acme:JR0"
    assert first.description == "Build Python services. 6 month internship."
    assert first.posted_at.date().isoformat() == "2026-11-15"
    assert first.url.endswith("Job-0_JR0")


def test_workday_location_labels():
    from app.ingest.sources import _workday_location

    assert _workday_location("India, Pune") == "India, Pune"
    assert _workday_location("Mumbai, Nirlon Knowledge Park") == "Mumbai, Nirlon Knowledge Park, India"
    assert _workday_location("Remote-Philippines") == "Remote-Philippines (also India)"
    assert _workday_location("") == "India"


def test_retry_delay_honours_retry_after_and_backs_off():
    assert sources._retry_delay(httpx.Response(429, headers={"Retry-After": "30"}), 0) == 30
    assert sources._retry_delay(httpx.Response(429, headers={"Retry-After": "9999"}), 0) == sources.WORKDAY_MAX_WAIT
    assert [sources._retry_delay(httpx.Response(429), a) for a in range(4)] == [5, 10, 20, 40]
    assert sources._retry_delay(None, 1) == 10  # dropped connection: same back-off


def test_a_429_pauses_every_workday_request(monkeypatch):
    monkeypatch.setattr(sources, "_retry_delay", lambda resp, attempt: 0.2)
    sent = []

    def handler(request: httpx.Request) -> httpx.Response:
        sent.append((request.url.path, asyncio.get_event_loop().time()))
        if request.url.path == "/a" and len(sent) == 1:
            return httpx.Response(429)
        return httpx.Response(200, json={})

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            first = asyncio.create_task(sources._workday_send(client, "GET", "https://x.test/a"))
            await asyncio.sleep(0.05)  # /a has been rate-limited by now
            await sources._workday_send(client, "GET", "https://x.test/b")
            await first

    asyncio.run(run())
    start = sent[0][1]
    assert sorted(path for path, _ in sent) == ["/a", "/a", "/b"]
    assert all(t - start >= 0.19 for _, t in sent[1:])  # nothing was sent during the pause
