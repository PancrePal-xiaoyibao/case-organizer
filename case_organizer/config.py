import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()


def _env_first(*keys: str, default: str = "") -> str:
    for key in keys:
        value = os.getenv(key)
        if value:
            return value
    return default


def _resolve_results_base() -> str:
    base = _env_first(
        "MINERU_RESULTS_BASE",
        "MINERU_API_BASE_URL",
        default="https://mineru.net/api/v4",
    ).rstrip("/")
    if "/api/" in base:
        return base
    return f"{base}/api/v4"


def _resolve_extract_batch_endpoint() -> str:
    explicit = os.getenv("MINERU_EXTRACT_BATCH_ENDPOINT")
    if explicit:
        return explicit
    base = _resolve_results_base()
    return f"{base}/extract/task/batch"


def _resolve_file_urls_endpoint() -> str:
    explicit = os.getenv("MINERU_FILE_URLS_ENDPOINT")
    if explicit:
        return explicit
    base = _resolve_results_base()
    return f"{base}/file-urls/batch"


class Settings(BaseModel):
    mineru_api_token: str = Field(
        default_factory=lambda: _env_first("MINERU_API_TOKEN", "MINERU_API_KEY")
    )
    mineru_extract_batch_endpoint: str = Field(
        default_factory=_resolve_extract_batch_endpoint
    )
    mineru_file_urls_endpoint: str = Field(
        default_factory=_resolve_file_urls_endpoint
    )
    mineru_results_base: str = Field(
        default_factory=_resolve_results_base
    )
    poll_interval_seconds: int = Field(
        default_factory=lambda: int(os.getenv("POLL_INTERVAL_SECONDS", "5"))
    )
    workspace_dir: Path = Field(
        default_factory=lambda: Path(os.getenv("WORKSPACE_DIR", "./workspace"))
    )
