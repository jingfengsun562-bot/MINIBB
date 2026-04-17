from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    fmp_api_key: str = ""
    anthropic_api_key: str = ""
    openbb_pat: str = ""
    claude_model: str = "claude-sonnet-4-6"

    fmp_base_url: str = "https://financialmodelingprep.com/stable"
    cache_ttl_seconds: int = 86400  # 24 hours


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
