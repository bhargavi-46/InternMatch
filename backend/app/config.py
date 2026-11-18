from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # "local" starts an embedded Postgres + pgvector in backend/.pgdata (no account needed).
    database_url: str | None = None
    groq_api_key: str | None = None
    groq_model: str = "openai/gpt-oss-120b"
    adzuna_app_id: str | None = None
    adzuna_app_key: str | None = None
    cors_origins: str = "http://localhost:3000"


settings = Settings()
