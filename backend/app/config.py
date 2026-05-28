"""
Configuration Management - PostgreSQL version
"""
import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # PostgreSQL
    pg_host: str = os.environ.get("PG_HOST", "localhost")
    pg_port: str = os.environ.get("PG_PORT", "5432")
    pg_name: str = os.environ.get("PG_NAME", "host_inspection")
    pg_user: str = os.environ.get("PG_USER", "postgres")
    pg_pass: str = os.environ.get("PG_PASS", "admin@123")

    # Alert thresholds
    cpu_warning_threshold: float = 70.0
    cpu_critical_threshold: float = 80.0
    memory_warning_threshold: float = 70.0
    memory_critical_threshold: float = 80.0
    storage_warning_threshold: float = 60.0
    storage_critical_threshold: float = 70.0

    # Collection
    inspection_interval_minutes: int = 5
    api_prefix: str = "/api"

    class Config:
        env_file = ".env"


settings = Settings()
