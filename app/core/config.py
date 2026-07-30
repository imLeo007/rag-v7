from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):

    database_url: str

    embedding_model: str
    embedding_dimension: int

    reranker_model_name: str
    rerank_candidate_k: int

    gemini_api_key: str
    gemini_model: str

    groq_api_key: str
    groq_model: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()