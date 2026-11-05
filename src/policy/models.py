from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from src.quotes.models import Quote


@dataclass
class ProcurementPolicy:
    """Buyer's policy constraints derived from MASTER-HANDOFF and Section 5.1."""
    budget_ceiling_usd: float = 25000.0
    required_delivery_days: int = 14
    min_vendor_headcount: int = 10
    allowed_payment_terms: List[str] = field(default_factory=lambda: ["Net 30", "Net 45", "Net 60"])
    currency: str = "USD"


@dataclass
class PolicyEvaluationResult:
    """Result of evaluating a quote against policy rules."""
    display_label: str
    is_compliant: bool
    total_price: float
    unit_price: float
    lead_time_days: int
    quote: Quote
    checks: Dict[str, str] = field(default_factory=dict)
    exception_reason: Optional[str] = None
    rank: Optional[int] = None
    label: str = "SIMULATED"

    def to_screen_dict(self) -> Dict[str, Any]:
        """User/screen-facing representation: ONLY display labels, no real names."""
        return {
            "rank": self.rank,
            "display_label": self.display_label,
            "is_compliant": self.is_compliant,
            "total_price": self.total_price,
            "unit_price": self.unit_price,
            "lead_time_days": self.lead_time_days,
            "checks": self.checks,
            "exception_reason": self.exception_reason,
            "label": "SIMULATED"
        }

    def to_contract_decision(self) -> Dict[str, Any]:
        """Matches Person 1's policy_decision contract: {label, approved, display_label, reason}."""
        reason_text = (
            f"Quote is within budget (${self.total_price:,.2f}) and delivery window ({self.lead_time_days}d)."
            if self.is_compliant
            else (self.exception_reason or "Non-compliant quote")
        )
        return {
            "label": "SIMULATED",
            "approved": self.is_compliant,
            "display_label": self.display_label,
            "reason": reason_text
        }

