"""Exceptions for Crustdata client and operations."""


class CrustdataAPIError(Exception):
    """Base exception for Crustdata API interactions."""
    def __init__(self, message: str, status_code: int | None = None, response_body: str | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body


class CrustdataAuthError(CrustdataAPIError):
    """HTTP 401: Authentication failure. API key invalid or missing."""
    pass


class CrustdataCreditsExhaustedError(CrustdataAPIError):
    """HTTP 402: Credits exhausted.

    Builder handbook / rules: A retry will not help. Check balance with
    GET /account/credits, then notify the Crustdata team.
    """
    pass


class CrustdataPlanGatedError(CrustdataAPIError):
    """HTTP 403: Forbidden / Plan-gated.

    The requested endpoint or field is not included in the current subscription plan.
    Do NOT retry.
    """
    pass


class CrustdataRateLimitError(CrustdataAPIError):
    """HTTP 429: Rate limit exceeded after retrying with backoff."""
    pass


class CrustdataSecurityError(CrustdataAPIError):
    """Security check failure, e.g. key file not git-ignored."""
    pass


class CrustdataBudgetExceededError(CrustdataAPIError):
    """Batch operation exceeds the safety credit budget."""
    pass
