"""Crustdata API client with backoff, plan-gate guards, and key protection."""

from __future__ import annotations

import logging
import os
import subprocess
import time
from typing import Any, Dict, List, Optional
import urllib.parse

import requests

from .exceptions import (
    CrustdataAPIError,
    CrustdataAuthError,
    CrustdataBudgetExceededError,
    CrustdataCreditsExhaustedError,
    CrustdataPlanGatedError,
    CrustdataRateLimitError,
    CrustdataSecurityError,
)

logger = logging.getLogger("crustdata.client")


def mask_key(key: Optional[str]) -> str:
    """Safely mask API key for logging and string representation."""
    if not key:
        return "<not set>"
    if len(key) <= 8:
        return "***"
    return f"{key[:4]}...{key[-4:]}"


def verify_file_git_ignored(filepath: str) -> bool:
    """Verify that a local file holding secrets is properly git-ignored.

    Returns True if git ignores the file, False otherwise.
    """
    if not os.path.exists(filepath):
        return True
    try:
        res = subprocess.run(
            ["git", "check-ignore", "-q", filepath],
            capture_output=True,
            text=True,
            check=False,
        )
        return res.returncode == 0
    except Exception as exc:
        logger.warning("Could not verify git-ignore status via git command: %s", exc)
        return False


def load_api_key_from_env(env_var: str = "CRUSTDATA_API_KEY", env_file: Optional[str] = None) -> Optional[str]:
    """Read API key only from local environment, verifying any secret file is git-ignored."""
    # If a secret file path is specified, confirm it is git-ignored before reading
    if env_file and os.path.exists(env_file):
        if not verify_file_git_ignored(env_file):
            raise CrustdataSecurityError(
                f"Security violation: File '{env_file}' containing credentials is NOT git-ignored! "
                "Refusing to read secrets from an unignored file."
            )
        # Parse simple KEY=VALUE
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    if k.strip() == env_var:
                        return v.strip().strip("'\"")

    key = os.environ.get(env_var) or os.environ.get("CRUSTDATA_KEY")
    return key


class CrustdataClient:
    """Client for Crustdata API (v2025-11-01).

    Enforces:
    - Base URL: https://api.crustdata.com
    - Headers: Authorization Bearer <KEY>, x-api-version: 2025-11-01
    - 429 retry with exponential backoff / retry-after
    - 402 stop immediately (credits exhausted)
    - 403 stop immediately (plan-gated field or endpoint)
    - Key masking in logs and repr
    - Live-run gating (must be explicitly enabled with allow_live=True)
    """

    BASE_URL = "https://api.crustdata.com"
    API_VERSION = "2025-11-01"

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        allow_live: bool = False,
        max_retries: int = 3,
        backoff_base: float = 1.0,
        session: Optional[requests.Session] = None,
    ):
        self.api_key = api_key or load_api_key_from_env()
        self.base_url = (base_url or self.BASE_URL).rstrip("/")
        self.allow_live = allow_live
        self.max_retries = max_retries
        self.backoff_base = backoff_base
        self.session = session or requests.Session()

    def __repr__(self) -> str:
        return (
            f"CrustdataClient(base_url='{self.base_url}', "
            f"api_version='{self.API_VERSION}', "
            f"key={mask_key(self.api_key)}, "
            f"allow_live={self.allow_live})"
        )

    def _get_headers(self) -> Dict[str, str]:
        headers = {
            "x-api-version": self.API_VERSION,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Send HTTP request to Crustdata API with retry on 429 and hard stop on 402/403."""
        if not self.allow_live:
            raise CrustdataAPIError(
                "Live Crustdata calls are disabled. Live calls require explicit permission from "
                "the project owner (bratadeepsarkar123) and allow_live=True."
            )

        if not self.api_key:
            raise CrustdataAuthError(
                "CRUSTDATA_API_KEY environment variable is not set. Cannot make live API calls."
            )

        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = self._get_headers()

        attempts = 0
        while attempts <= self.max_retries:
            attempts += 1
            try:
                logger.debug("Crustdata %s %s (attempt %d)", method, endpoint, attempts)
                response = self.session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    json=json_data,
                    timeout=30.0,
                )
            except requests.RequestException as e:
                if attempts > self.max_retries:
                    raise CrustdataAPIError(f"Network error calling Crustdata {endpoint}: {e}") from e
                time.sleep(self.backoff_base * (2 ** (attempts - 1)))
                continue

            status = response.status_code

            # 200 OK
            if 200 <= status < 300:
                try:
                    return response.json()
                except Exception:
                    return {"raw": response.text}

            # 401 Unauthorized
            if status == 401:
                raise CrustdataAuthError(
                    f"HTTP 401: Invalid API key or missing Bearer token when accessing {endpoint}."
                )

            # 402 Payment Required - Stop immediately
            if status == 402:
                logger.error("Crustdata HTTP 402: Credits exhausted on %s. Stopping immediately.", endpoint)
                raise CrustdataCreditsExhaustedError(
                    "HTTP 402: Crustdata credits exhausted. A retry will not help. "
                    "Check balance with GET /account/credits, then notify the Crustdata team."
                )

            # 403 Forbidden - Stop immediately (Plan-gated)
            if status == 403:
                logger.error("Crustdata HTTP 403: Plan-gated field or endpoint on %s. Stopping immediately.", endpoint)
                raise CrustdataPlanGatedError(
                    f"HTTP 403: Endpoint or requested field at '{endpoint}' is plan-gated on your account. "
                    "Do NOT retry this call. (Refer to MASTER-HANDOFF section 7 for plan-gated fields)."
                )

            # 429 Too Many Requests - Back off and retry
            if status == 429:
                if attempts > self.max_retries:
                    raise CrustdataRateLimitError(
                        f"HTTP 429: Rate limit exceeded on {endpoint} after {self.max_retries} retries."
                    )
                # Check for retry-after or x-ratelimit-reset
                retry_after_str = response.headers.get("Retry-After") or response.headers.get("x-ratelimit-reset")
                try:
                    sleep_time = float(retry_after_str) if retry_after_str else self.backoff_base * (2 ** (attempts - 1))
                except (ValueError, TypeError):
                    sleep_time = self.backoff_base * (2 ** (attempts - 1))

                # Cap max sleep to reasonable hackathon limit (e.g. 15s)
                sleep_time = min(sleep_time, 15.0)
                logger.warning("Crustdata 429 on %s; backing off for %.2f seconds", endpoint, sleep_time)
                time.sleep(sleep_time)
                continue

            # Other 4xx / 5xx errors
            body = response.text[:200]
            raise CrustdataAPIError(
                f"HTTP {status} calling Crustdata {endpoint}: {body}",
                status_code=status,
                response_body=response.text,
            )

        raise CrustdataRateLimitError(f"HTTP 429: Rate limit exceeded after {self.max_retries} retries.")

    def get_account_credits(self) -> Dict[str, Any]:
        """Check credit balance: GET /account/credits (Free)."""
        return self._request("GET", "/account/credits")

    def company_search(
        self,
        query: Optional[str] = None,
        filters: Optional[List[Dict[str, Any]]] = None,
        limit: int = 100,
        ranked: bool = True,
    ) -> Dict[str, Any]:
        """POST /company/search.

        Ranked search (search.query) first, location filters as hard limits.
        Single window of up to 100 results, no paging.
        """
        payload: Dict[str, Any] = {"limit": min(limit, 100)}
        if ranked and query:
            payload["search"] = {"query": query}
        elif query:
            payload["query"] = query

        if filters:
            payload["filters"] = filters

        return self._request("POST", "/company/search", json_data=payload)

    def company_autocomplete(self, query: str) -> Dict[str, Any]:
        """POST /company/search/autocomplete (Free).

        Resolves closed-set industry or entity names before filtering.
        """
        payload = {"query": query}
        return self._request("POST", "/company/search/autocomplete", json_data=payload)

    def company_identify(
        self,
        names: Optional[List[str]] = None,
        domains: Optional[List[str]] = None,
        fields: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """POST /company/identify (Free).

        SAFETY GUARD: Master handoff section 7 specifies that headcount and locations
        are plan-gated (403) on identify. Never request headcount or locations on identify!
        """
        if fields:
            forbidden = {"headcount", "locations", "locations.headquarters", "headcount.total"}
            if any(f in forbidden for f in fields):
                raise ValueError(
                    "Violation: Never request 'headcount' or 'locations' on company/identify! "
                    "They are plan-gated (403) on identify. Request them on company/enrich only."
                )

        payload: Dict[str, Any] = {}
        if names:
            payload["names"] = names
        if domains:
            payload["domains"] = domains
        if fields:
            payload["fields"] = fields

        return self._request("POST", "/company/identify", json_data=payload)

    def company_enrich(
        self,
        company_id: Optional[int] = None,
        domain: Optional[str] = None,
        fields: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """POST /company/enrich (Costs 2 credits per match).

        Used for headcount, locations, and basic_info.description.
        """
        payload: Dict[str, Any] = {}
        if company_id is not None:
            payload["crustdata_company_id"] = company_id
        elif domain is not None:
            payload["domain"] = domain
        else:
            raise ValueError("Either company_id or domain must be specified for company/enrich.")

        # Default fields to request per section 7
        if fields is None:
            payload["fields"] = ["headcount", "locations", "basic_info"]
        else:
            payload["fields"] = fields

        return self._request("POST", "/company/enrich", json_data=payload)
