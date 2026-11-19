from app.ingest.run import unique_postings
from app.ingest.sources import Posting


def posting(external_id: str, location: str, source: str = "workday") -> Posting:
    return Posting(source=source, external_id=external_id, company="Acme", title="SDE Intern", location=location,
                   is_remote=False, employment_type=None, description="", url="https://acme.test/job", posted_at=None)


def test_unique_postings_drops_repeated_ids_and_keeps_the_rest():
    postings = [posting("acme:JR1", "Pune"), posting("acme:JR2", "Pune"), posting("acme:JR1", "Bengaluru"),
                posting("acme:JR1", "Pune", source="greenhouse")]
    result = unique_postings(postings)
    assert [(p.source, p.external_id) for p in result] == [
        ("workday", "acme:JR1"), ("workday", "acme:JR2"), ("greenhouse", "acme:JR1")
    ]
    assert result[0].location == "Bengaluru"  # the last copy wins
