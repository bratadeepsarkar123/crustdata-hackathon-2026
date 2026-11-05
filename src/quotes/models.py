from dataclasses import dataclass, field
from typing import Dict, Any, Optional


class QuoteValidationError(Exception):
    """Raised when a quote does not adhere to the required schema or contains invalid data."""
    pass


@dataclass
class Quote:
    """Represents a supplier quotation conforming to MASTER-HANDOFF Section 6.
    
    Contract shape:
    { display_label, unit_price, lead_time_days, label: "SIMULATED" }
    """
    display_label: str
    unit_price: float
    lead_time_days: int
    label: str = "SIMULATED"
    quantity: int = 500
    total_price: Optional[float] = None
    payment_terms: str = "Net 30"
    source: str = "SIMULATED_DATASET_STEP_5B"
    raw_data: Dict[str, Any] = field(default_factory=dict)
    _internal: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        # Validate display label formatting (Neutral labels only, e.g. Supplier 1)
        if not self.display_label or not isinstance(self.display_label, str):
            raise QuoteValidationError("Quote display_label must be a non-empty string.")
        
        # Enforce explicit SIMULATED label
        if self.label != "SIMULATED":
            raise QuoteValidationError(
                f"Quote label must be explicitly 'SIMULATED', got '{self.label}'."
            )

        # Validate numeric constraints
        try:
            self.unit_price = float(self.unit_price)
            if self.unit_price <= 0:
                raise QuoteValidationError(f"unit_price must be positive, got {self.unit_price}")
        except (ValueError, TypeError):
            raise QuoteValidationError(f"Invalid unit_price: {self.unit_price}")

        try:
            self.lead_time_days = int(self.lead_time_days)
            if self.lead_time_days < 0:
                raise QuoteValidationError(f"lead_time_days cannot be negative, got {self.lead_time_days}")
        except (ValueError, TypeError):
            raise QuoteValidationError(f"Invalid lead_time_days: {self.lead_time_days}")

        if self.quantity <= 0:
            raise QuoteValidationError(f"quantity must be positive, got {self.quantity}")

        if self.total_price is None:
            self.total_price = round(self.unit_price * self.quantity, 2)
        else:
            self.total_price = float(self.total_price)

    def to_contract_dict(self) -> Dict[str, Any]:
        """Returns the minimal JSON shape expected by Person 1's frozen contract."""
        return {
            "display_label": self.display_label,
            "unit_price": self.unit_price,
            "lead_time_days": self.lead_time_days,
            "label": "SIMULATED"
        }

    def to_full_dict(self) -> Dict[str, Any]:
        """Returns full representation including provenance and internal verification fields."""
        return {
            "display_label": self.display_label,
            "unit_price": self.unit_price,
            "quantity": self.quantity,
            "total_price": self.total_price,
            "lead_time_days": self.lead_time_days,
            "payment_terms": self.payment_terms,
            "label": "SIMULATED",
            "source": self.source,
            "_internal": self._internal
        }

