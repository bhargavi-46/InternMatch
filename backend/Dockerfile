FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.10.8 /uv /uvx /bin/

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --frozen --no-dev --no-install-project

COPY app ./app
# Bake the embedding model into the image so cold starts don't download it.
RUN uv run --no-sync python -c "from app.embeddings import warm_up; warm_up()"

ENV PORT=8000
EXPOSE 8000
CMD ["sh", "-c", "uv run --no-sync uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
