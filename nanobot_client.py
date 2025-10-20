import logging
from typing import Any, Dict, Optional

import requests


logger = logging.getLogger(__name__)


class NanobotError(Exception):
    """Base exception for Nanobot client errors."""


class NanobotResponseError(NanobotError):
    """Raised when Nanobot returns an unexpected payload."""


class NanobotClient:
    """Minimal HTTP client for interacting with Nanobot agents."""

    def __init__(self, base_url: str, session: Optional[requests.Session] = None):
        if not base_url:
            raise ValueError("Missing Nanobot base URL")

        self._base_url = base_url.rstrip("/")
        self._session = session or requests.Session()

    def classify_invoice(self, agent: str, text: str) -> Dict[str, Any]:
        payload = {
            "mode": "agent",
            "name": agent,
            "input": text,
            "chat": False,
        }
        return self._call("/api/call", payload)

    def triage_invoice(self, agent: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        body = {
            "mode": "agent",
            "name": agent,
            "input": payload,
            "chat": False,
        }
        return self._call("/api/call", body)

    def _call(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self._base_url}{path}"

        try:
            response = self._session.post(url, json=payload, timeout=30)
        except requests.RequestException as exc:
            raise NanobotError(str(exc)) from exc

        if response.status_code != 200:
            raise NanobotError(f"Nanobot returned status {response.status_code}: {response.text.strip()}")

        try:
            data = response.json().get("response")
        except ValueError as exc:
            raise NanobotResponseError("Failed to decode Nanobot response as JSON") from exc

        if not data or "output" not in data:
            raise NanobotResponseError("Nanobot response missing output field")

        return data["output"]
