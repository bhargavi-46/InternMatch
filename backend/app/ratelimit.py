import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request


class RateLimiter:
    """Small in-memory sliding-window limiter, per client IP. Protects the free Groq quota on a public demo."""

    def __init__(self, max_calls: int, window_seconds: int):
        self.max_calls = max_calls
        self.window = window_seconds
        self._calls: dict[str, deque[float]] = defaultdict(deque)

    def __call__(self, request: Request) -> None:
        key = request.client.host if request.client else "unknown"
        now = time.monotonic()
        calls = self._calls[key]
        while calls and now - calls[0] > self.window:
            calls.popleft()
        if len(calls) >= self.max_calls:
            raise HTTPException(429, "Too many AI requests. Please wait a few minutes and try again.")
        calls.append(now)


llm_rate_limit = RateLimiter(max_calls=30, window_seconds=600)
