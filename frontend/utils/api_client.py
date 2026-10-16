"""HTTP client for the laptop price prediction backend."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv((PROJECT_ROOT / ".env").resolve())


class APIClientError(RuntimeError):
    """Expected API/network failure suitable for displaying in the UI."""


class APIClient:
    """Call the FastAPI prediction service over HTTP."""

    def __init__(
        self,
        base_url: str | None = None,
        *,
        timeout: float = 15.0,
        session: requests.Session | None = None,
    ) -> None:
        configured_url = base_url or os.getenv("BACKEND_URL")
        if not configured_url:
            raise APIClientError("BACKEND_URL is not configured.")

        self.base_url = self._normalize_base_url(configured_url)
        self.timeout = timeout
        self.session = session or requests.Session()

    @staticmethod
    def _normalize_base_url(base_url: str) -> str:
        normalized = base_url.rstrip("/")
        if not normalized.endswith("/api/v1"):
            normalized = f"{normalized}/api/v1"
        return normalized

    def check_health(self) -> dict[str, Any] | None:
        """Return backend health data, or raise a structured client error."""
        return self._request("GET", "/health")

    def predict_price(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        """Submit a laptop payload and return the prediction response."""
        return self._request("POST", "/predict", json=payload)

    def _request(
        self,
        method: str,
        path: str,
        **kwargs: Any,
    ) -> dict[str, Any] | None:
        url = f"{self.base_url}{path}"
        try:
            response = self.session.request(method, url, timeout=self.timeout, **kwargs)
        except requests.RequestException as exc:
            raise APIClientError(
                "Could not connect to the prediction backend. "
                "Check that the FastAPI service is running."
            ) from exc

        if not response.ok:
            detail = self._response_detail(response)
            raise APIClientError(
                f"Backend request failed ({response.status_code}): {detail}"
            )

        try:
            data = response.json()
        except ValueError as exc:
            raise APIClientError("The backend returned an invalid JSON response.") from exc

        if not isinstance(data, dict):
            raise APIClientError("The backend returned an unexpected response format.")
        return data

    @staticmethod
    def _response_detail(response: requests.Response) -> str:
        try:
            payload = response.json()
        except ValueError:
            return response.text or "Unknown backend error"
        if isinstance(payload, dict) and payload.get("detail"):
            return str(payload["detail"])
        return response.text or "Unknown backend error"