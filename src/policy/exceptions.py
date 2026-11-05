import time
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from src.quotes.models import Quote


@dataclass
class ExceptionRecord:
    """Represents a quote or action routed to the exceptions queue."""
    display_label: str
    reason: str
    quote: Quote
    timestamp: float = field(default_factory=time.time)
    status: str = "EXCEPTION"
    label: str = "SIMULATED"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "display_label": self.display_label,
            "reason": self.reason,
            "status": self.status,
            "label": self.label,
            "timestamp": self.timestamp,
            "quote_summary": {
                "display_label": self.quote.display_label,
                "unit_price": self.quote.unit_price,
                "quantity": self.quote.quantity,
                "total_price": self.quote.total_price,
                "lead_time_days": self.quote.lead_time_days,
                "payment_terms": self.quote.payment_terms
            }
        }


class ExceptionsQueue:
    """Queue holding non-compliant quotes or edge cases requiring human-in-the-loop review."""

    def __init__(self):
        self._records: List[ExceptionRecord] = []

    def add_exception(self, display_label: str, reason: str, quote: Quote) -> ExceptionRecord:
        record = ExceptionRecord(
            display_label=display_label,
            reason=reason,
            quote=quote
        )
        self._records.append(record)
        return record

    def get_records(self) -> List[ExceptionRecord]:
        return list(self._records)

    def count(self) -> int:
        return len(self._records)

    def clear(self):
        self._records.clear()

