from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests


class ApiConnectionError(RuntimeError):
    """Raised when Streamlit cannot reach the FastAPI service."""


@dataclass
class ApiClient:
    """Small HTTP client for the project's FastAPI contract.

    Keeping HTTP details here makes the Streamlit UI independent from the
    transport implementation and makes it easier to test or replace the UI.
    """

    base_url: str
    token: str | None = None
    timeout: int = 90

    def request(self, method: str, path: str, **kwargs) -> requests.Response:
        headers = dict(kwargs.pop("headers", {}))
        if self.token:
            headers.setdefault("Authorization", f"Bearer {self.token}")

        try:
            return requests.request(
                method,
                f"{self.base_url.rstrip('/')}{path}",
                headers=headers,
                timeout=kwargs.pop("timeout", self.timeout),
                **kwargs,
            )
        except requests.RequestException as exc:
            raise ApiConnectionError(str(exc)) from exc

    def json(self, method: str, path: str, **kwargs) -> Any:
        response = self.request(method, path, **kwargs)
        response.raise_for_status()
        return response.json()
