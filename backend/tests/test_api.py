"""API checks that need neither a database nor an LLM (TestClient without `with` skips app startup)."""

import pytest
from fastapi.testclient import TestClient

from app import resume
from app.config import settings
from app.main import app
from app.ratelimit import RateLimiter

client = TestClient(app)


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_resume_rejects_non_pdf():
    resp = client.post("/resume/parse", files={"file": ("cv.txt", b"hello", "text/plain")})
    assert resp.status_code == 400


def test_resume_rejects_huge_file():
    resp = client.post("/resume/parse", files={"file": ("cv.pdf", b"%PDF" + b"0" * (5 * 1024 * 1024), "application/pdf")})
    assert resp.status_code == 413


def test_chat_without_groq_key_returns_503(monkeypatch):
    monkeypatch.setattr(settings, "groq_api_key", None)
    resp = client.post("/agent/chat", json={"thread_id": "thread-123", "message": "hi"})
    assert resp.status_code == 503
    assert "GROQ_API_KEY" in resp.json()["detail"]


def test_redacts_contact_details_before_llm():
    text = resume.redact_contact_details("Reach me at jane.doe@mail.com or +91 98765 43210.")
    assert "jane.doe" not in text and "98765" not in text


def test_rate_limiter_blocks_after_limit():
    from fastapi import HTTPException
    from starlette.requests import Request

    limiter = RateLimiter(max_calls=2, window_seconds=60)
    request = Request({"type": "http", "client": ("1.2.3.4", 1), "headers": []})
    limiter(request)
    limiter(request)
    with pytest.raises(HTTPException) as exc:
        limiter(request)
    assert exc.value.status_code == 429
