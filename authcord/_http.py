"""Internal HTTP client wrapper with retry logic."""

from __future__ import annotations
import time
from typing import Any, Dict, Optional
import httpx

from .exceptions import APIError, AuthenticationError, NetworkError, RateLimitError


class HTTPClient:
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://authcord.dev",
        timeout: float = 30.0,
        max_retries: int = 3,
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.max_retries = max_retries
        self._client = httpx.Client(
            timeout=timeout,
            headers={
                "X-API-Key": api_key,
                "Content-Type": "application/json",
                "User-Agent": "AuthCord-Python-SDK/1.0.0",
            },
        )

    def _handle_response(self, response: httpx.Response) -> Dict[str, Any]:
        if response.status_code == 401:
            raise AuthenticationError("Invalid API key")
        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", "60"))
            raise RateLimitError(retry_after=retry_after)
        if response.status_code >= 400:
            try:
                data = response.json()
                msg = data.get("message", data.get("error", f"HTTP {response.status_code}"))
            except Exception:
                msg = f"HTTP {response.status_code}"
            raise APIError(msg, status_code=response.status_code)
        return response.json()

    def request(self, method: str, path: str, **kwargs: Any) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        last_exc: Optional[Exception] = None
        for attempt in range(self.max_retries):
            try:
                response = self._client.request(method, url, **kwargs)
                return self._handle_response(response)
            except RateLimitError:
                raise
            except APIError:
                raise
            except (httpx.NetworkError, httpx.TimeoutException) as e:
                last_exc = e
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                raise NetworkError(f"Request failed after {self.max_retries} attempts: {e}")
        raise NetworkError("Request failed")

    def get(self, path: str, **kwargs: Any) -> Dict[str, Any]:
        return self.request("GET", path, **kwargs)

    def post(self, path: str, **kwargs: Any) -> Dict[str, Any]:
        return self.request("POST", path, **kwargs)

    def close(self) -> None:
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
