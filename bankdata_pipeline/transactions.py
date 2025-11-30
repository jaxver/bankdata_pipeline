from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import requests

from .config import PipelineSettings

_SAMPLE_FILE = Path(__file__).resolve().parents[1] / "data" / "samples" / "transactions_sample.json"


def fetch_transactions(access_token: str, settings: PipelineSettings) -> Dict[str, Any]:
    """Download the latest transactions payload or return the bundled sample."""

    if settings.sample_mode:
        return json.loads(_SAMPLE_FILE.read_text("utf-8"))

    url = (
        f"{settings.api.base_url.rstrip('/')}/accounts/{settings.api.account_id}/transactions/"
    )
    headers = {"accept": "application/json", "Authorization": f"Bearer {access_token}"}
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    return response.json()


def persist_transactions(payload: Dict[str, Any], settings: PipelineSettings) -> Path:
    """Write the downloaded payload to the extracts folder."""

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    path = settings.storage.extracts_dir / f"{timestamp}_transactions_summary.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


__all__ = ["fetch_transactions", "persist_transactions"]
