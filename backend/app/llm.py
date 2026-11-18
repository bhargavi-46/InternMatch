from langchain_core.runnables import Runnable
from langchain_groq import ChatGroq
from pydantic import BaseModel

from app.config import settings


class LLMNotConfigured(RuntimeError):
    pass


def get_llm() -> ChatGroq:
    if not settings.groq_api_key:
        raise LLMNotConfigured("GROQ_API_KEY is not set in backend/.env (free key: https://console.groq.com/keys).")
    return ChatGroq(
        model=settings.groq_model,
        api_key=settings.groq_api_key,
        temperature=0,
        max_retries=2,
        reasoning_effort="low",  # gpt-oss models: keeps answers fast and within free-tier token limits
    )


def structured_llm(schema: type[BaseModel]) -> Runnable:
    """An LLM whose reply is guaranteed to match `schema`.

    strict=True turns on Groq's constrained decoding for gpt-oss models. Without it the model sometimes
    wraps its answer in the schema itself ({"properties": {...}}), which then fails validation.
    """
    return get_llm().with_structured_output(schema, method="json_schema", strict=True)
