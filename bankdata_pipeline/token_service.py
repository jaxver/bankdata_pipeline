from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Optional

import requests

from .config import PipelineSettings

_TOKEN_NEW_SUFFIX = "/token/new/"
_TOKEN_REFRESH_SUFFIX = "/token/refresh/"


class TokenService:
    """Handles requesting and refreshing tokens while caching them on disk."""

    def __init__(self, settings: PipelineSettings) -> None:
        self.settings = settings
        self.session = requests.Session()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def ensure_access_token(self) -> str:
        """Return a valid access token, refreshing or requesting as needed."""

        cached = self._read_cached_token()
        if cached and not self._is_expired(cached, "access_expires", default_seconds=3600):
            return cached["access"]

        if (
            cached
            and "refresh" in cached
            and not self._is_expired(cached, "refresh_expires", default_seconds=2592000)
        ):
            refreshed = self._refresh_token(cached["refresh"])
            self._write_cached_token(refreshed)
            return refreshed["access"]

        fresh = self._request_new_token()
        self._write_cached_token(fresh)
        return fresh["access"]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _request_new_token(self) -> Dict[str, Any]:
        payload = {
            "secret_id": self.settings.api.secret_id,
            "secret_key": self.settings.api.secret_key,
        }
        response = self.session.post(self._api_url(_TOKEN_NEW_SUFFIX), json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        data["token_time"] = datetime.now(timezone.utc).isoformat()
        return data

    def _refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        payload = {"refresh": refresh_token}
        response = self.session.post(self._api_url(_TOKEN_REFRESH_SUFFIX), json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        data["token_time"] = datetime.now(timezone.utc).isoformat()
        return data

    def _api_url(self, suffix: str) -> str:
        base = self.settings.api.base_url.rstrip("/")
        return f"{base}{suffix}"

    def _is_expired(self, token: Dict[str, Any], duration_field: str, default_seconds: int) -> bool:
        stamp = token.get("token_time")
        expires_in = token.get(duration_field, default_seconds)
        if not stamp:
            return True
        try:
            issued = datetime.fromisoformat(stamp)
            if issued.tzinfo is None:
                issued = issued.replace(tzinfo=timezone.utc)
        except ValueError:
            return True
        # tokens record seconds until expiry at the time of issue
        return datetime.now(timezone.utc) - issued >= timedelta(seconds=expires_in)

    def _read_cached_token(self) -> Optional[Dict[str, Any]]:
        path = self.settings.storage.token_cache
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text("utf-8"))
        except json.JSONDecodeError:
            return None

    def _write_cached_token(self, token: Dict[str, Any]) -> None:
        path: Path = self.settings.storage.token_cache
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(token, indent=2), encoding="utf-8")


__all__ = ["TokenService"]
