"""Crustdata API integration package for supplier discovery and verification."""

from .client import CrustdataClient
from .exceptions import (
    CrustdataAPIError,
    CrustdataAuthError,
    CrustdataCreditsExhaustedError,
    CrustdataPlanGatedError,
    CrustdataRateLimitError,
)
from .credits import CreditGuard, check_account_credits, calculate_batch_cost

__all__ = [
    "CrustdataClient",
    "CrustdataAPIError",
    "CrustdataAuthError",
    "CrustdataCreditsExhaustedError",
    "CrustdataPlanGatedError",
    "CrustdataRateLimitError",
    "CreditGuard",
    "check_account_credits",
    "calculate_batch_cost",
]
