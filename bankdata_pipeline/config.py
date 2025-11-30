from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union

from dotenv import load_dotenv


@dataclass(frozen=True)
class ApiSettings:
    base_url: str
    account_id: str
    secret_id: str
    secret_key: str


@dataclass(frozen=True)
class StorageSettings:
    root: Path
    extracts_dir: Path
    analysis_dir: Path
    token_cache: Path


@dataclass(frozen=True)
class PipelineSettings:
    api: ApiSettings
    storage: StorageSettings
    sample_mode: bool = False


def _ensure_directory(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def load_settings(env_file: Optional[Union[str, Path]] = None) -> PipelineSettings:
    """Load pipeline settings from environment variables / optional env file."""

    env_candidate = env_file or os.environ.get("BANKDATA_ENV_FILE")
    if env_candidate:
        load_dotenv(dotenv_path=env_candidate, override=False)
    else:
        load_dotenv(override=False)

    def _require(name: str) -> str:
        value = os.environ.get(name)
        if not value:
            raise RuntimeError(f"Missing required environment variable: {name}")
        return value

    api = ApiSettings(
        base_url=os.environ.get("BANKDATA_API_BASE", "https://bankaccountdata.gocardless.com/api/v2"),
        account_id=_require("BANKDATA_ACCOUNT_ID"),
        secret_id=_require("BANKDATA_SECRET_ID"),
        secret_key=_require("BANKDATA_SECRET_KEY"),
    )

    storage_root = Path(os.environ.get("BANKDATA_STORAGE_ROOT", "runtime"))
    extracts_dir = _ensure_directory(storage_root / "extracts")
    analysis_dir = _ensure_directory(storage_root / "analysis")
    token_cache_env = os.environ.get("BANKDATA_TOKEN_CACHE")
    token_cache = Path(token_cache_env) if token_cache_env else (storage_root / "tokens" / "access_token.json")
    _ensure_directory(token_cache.parent)

    storage = StorageSettings(
        root=_ensure_directory(storage_root),
        extracts_dir=extracts_dir,
        analysis_dir=analysis_dir,
        token_cache=token_cache,
    )

    sample_mode = os.environ.get("BANKDATA_SAMPLE_MODE", "false").lower() in {"1", "true", "yes"}

    return PipelineSettings(api=api, storage=storage, sample_mode=sample_mode)
