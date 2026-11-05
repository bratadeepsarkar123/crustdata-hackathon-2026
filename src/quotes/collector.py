import json
import os
from typing import List, Dict, Any, Optional
from .models import Quote, QuoteValidationError


class QuoteCollector:
    """Loads, validates, and manages simulated supplier quotes with provenance tracking."""

    DEFAULT_DATA_PATH = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "data", "simulated", "supplier_quotes.json"
    )

    def __init__(self, data_path: Optional[str] = None):
        self.data_path = data_path or self.DEFAULT_DATA_PATH
        self._quotes_cache: Optional[List[Quote]] = None

    def load_quotes(self) -> List[Quote]:
        """Loads and validates quotes from the simulated dataset.
        
        Raises QuoteValidationError if the file cannot be read or JSON is invalid.
        """
        if not os.path.exists(self.data_path):
            raise FileNotFoundError(f"Simulated quotes file not found at: {self.data_path}")

        try:
            with open(self.data_path, "r", encoding="utf-8") as f:
                raw_items = json.load(f)
        except Exception as e:
            raise QuoteValidationError(f"Failed to read/parse simulated quotes JSON: {e}")

        if not isinstance(raw_items, list):
            raise QuoteValidationError(f"Expected list of quotes, got {type(raw_items).__name__}")

        quotes: List[Quote] = []
        for idx, item in enumerate(raw_items):
            if not isinstance(item, dict):
                raise QuoteValidationError(f"Quote at index {idx} is not an object/dict: {item}")
            
            quote = Quote(
                display_label=item.get("display_label", f"Supplier {idx+1}"),
                unit_price=item.get("unit_price", 0.0),
                lead_time_days=item.get("lead_time_days", 0),
                label=item.get("label", "SIMULATED"),
                quantity=item.get("quantity", 500),
                total_price=item.get("total_price"),
                payment_terms=item.get("payment_terms", "Net 30"),
                source=item.get("source", "SIMULATED_DATASET_STEP_5B"),
                raw_data=item,
                _internal=item.get("_internal", {})
            )
            quotes.append(quote)

        self._quotes_cache = quotes
        return quotes

    def get_quote_for_supplier(self, display_label: str) -> Optional[Quote]:
        """Look up a simulated quote by its neutral display label."""
        if self._quotes_cache is None:
            self.load_quotes()
        for q in self._quotes_cache:
            if q.display_label.lower() == display_label.lower():
                return q
        return None

