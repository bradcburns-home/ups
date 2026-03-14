from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    environment_name: str = "dev"
    google_cloud_project: str = "burns-agentspace"
    ups_dataset: str = "ups_prod"
    default_timezone: str = "America/Detroit"
    nut_host: str = "nut-prod"
    nut_port: int = 3493
    nut_ups_name: str = "eaton"
    log_level: str = "INFO"
    port: int = 8000

    model_config = {"extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
