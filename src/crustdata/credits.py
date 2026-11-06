"""Credit tracking, cost estimation, and safety budget guards for Crustdata."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from .exceptions import CrustdataBudgetExceededError

logger = logging.getLogger("crustdata.credits")

# No self-imposed run cap (owner decision, 2026-11-06). The real ceiling is the
# account balance, checked before any live call in discovery/service.py.
MAX_RUN_CREDIT_BUDGET = None

# Unit costs from Section 7 of MASTER-HANDOFF-supplier.md
COST_COMPANY_SEARCH_PER_RESULT = 0.03
COST_COMPANY_IDENTIFY = 0.0  # Free
COST_COMPANY_ENRICH_PER_MATCH = 2.0
COST_AUTOCOMPLETE = 0.0  # Free


def calculate_batch_cost(
    search_results_count: int = 10,
    identify_count: int = 10,
    enrich_count: int = 5,
    autocomplete_count: int = 1,
) -> float:
    """Calculate the estimated credit cost of a discovery and verification run.

    Costs per Section 7:
    - Search: 0.03 per result
    - Identify: Free (0.0)
    - Enrich: 2.0 per match
    - Autocomplete: Free (0.0)
    """
    cost = (
        (search_results_count * COST_COMPANY_SEARCH_PER_RESULT)
        + (identify_count * COST_COMPANY_IDENTIFY)
        + (enrich_count * COST_COMPANY_ENRICH_PER_MATCH)
        + (autocomplete_count * COST_AUTOCOMPLETE)
    )
    return round(cost, 2)


def check_account_credits(client) -> float:
    """Fetch current account credits from Crustdata.

    Returns the number of available credits as a float.
    """
    res = client.get_account_credits()
    # Typical Crustdata response shape: {"account": {"credits": 14995.18}} or {"credits": ...}
    credits = None
    if isinstance(res, dict):
        if "account" in res and isinstance(res["account"], dict) and "credits" in res["account"]:
            credits = res["account"]["credits"]
        elif "credits" in res:
            credits = res["credits"]

    if credits is None:
        raise ValueError(f"Could not parse credit balance from response: {res}")

    return float(credits)


class CreditGuard:
    """Tracks credit consumption for a run.

    max_budget=None means no run cap; only the account balance limits spending.
    """

    def __init__(self, max_budget: Optional[float] = MAX_RUN_CREDIT_BUDGET):
        self.max_budget = max_budget
        self.total_credits_used = 0.0

    def record_usage(self, credits: float, operation: str = "") -> None:
        """Record credit usage and verify we have not exceeded the budget, if one is set."""
        self.total_credits_used += credits
        logger.info("Crustdata spent %.2f credits on %s (Total run spend: %.2f / %s)",
                    credits, operation, self.total_credits_used,
                    "no cap" if self.max_budget is None else f"{self.max_budget:.2f}")
        if self.max_budget is not None and self.total_credits_used >= self.max_budget:
            raise CrustdataBudgetExceededError(
                f"Credit budget violation: Run has spent {self.total_credits_used:.2f} credits, "
                f"exceeding the safety limit of {self.max_budget:.2f} credits."
            )

    def estimate_and_check(self, estimated_credits: float) -> None:
        """Check if an upcoming operation would exceed the total run budget."""
        if self.max_budget is None:
            return
        projected = self.total_credits_used + estimated_credits
        if projected >= self.max_budget:
            raise CrustdataBudgetExceededError(
                f"Refusing execution: Projected credit spend ({projected:.2f}) "
                f"exceeds safety budget of {self.max_budget:.2f} credits."
            )
