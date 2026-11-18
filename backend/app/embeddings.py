"""Local, free sentence embeddings (BAAI/bge-small-en-v1.5 via ONNX, 384 dims, unit-normalised)."""

from functools import lru_cache
from pathlib import Path

import numpy as np
from fastembed import TextEmbedding

from app.models import Job

MODEL_NAME = "BAAI/bge-small-en-v1.5"
CACHE_DIR = Path(__file__).resolve().parent.parent / ".cache" / "fastembed"
# bge models retrieve better when short search queries carry this instruction.
QUERY_INSTRUCTION = "Represent this sentence for searching relevant passages: "


@lru_cache
def _model() -> TextEmbedding:
    return TextEmbedding(MODEL_NAME, cache_dir=str(CACHE_DIR))


def warm_up() -> None:
    _model()


def embed_documents(texts: list[str]) -> list[np.ndarray]:
    return list(_model().embed(texts, batch_size=32))


def embed_query(text: str) -> np.ndarray:
    return embed_documents([QUERY_INSTRUCTION + text])[0]


def job_text(job: Job) -> str:
    return f"{job.title} at {job.company}. {job.location}. {job.description[:3000]}"


def normalize(vector: np.ndarray) -> np.ndarray:
    norm = np.linalg.norm(vector)
    return vector / norm if norm else vector
