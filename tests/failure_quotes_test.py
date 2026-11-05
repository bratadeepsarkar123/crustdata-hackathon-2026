import unittest
from src.quotes.models import Quote, QuoteValidationError
from src.quotes.collector import QuoteCollector


class TestQuotesValidationAndFailures(unittest.TestCase):
    """Failure and contract compliance test suite for Quotes (Step 5b / AC-2)."""

    def setUp(self):
        self.collector = QuoteCollector()

    def test_load_deterministic_quotes(self):
        """Rule: Load Supplier 1 ($42) and Supplier 2 ($55) with exact deterministic figures."""
        quotes = self.collector.load_quotes()
        self.assertEqual(len(quotes), 2)

        q1 = quotes[0]
        self.assertEqual(q1.display_label, "Supplier 1")
        self.assertEqual(q1.unit_price, 42.0)
        self.assertEqual(q1.quantity, 500)
        self.assertEqual(q1.total_price, 21000.0)
        self.assertEqual(q1.lead_time_days, 10)
        self.assertEqual(q1.label, "SIMULATED")

        q2 = quotes[1]
        self.assertEqual(q2.display_label, "Supplier 2")
        self.assertEqual(q2.unit_price, 55.0)
        self.assertEqual(q2.quantity, 500)
        self.assertEqual(q2.total_price, 27500.0)
        self.assertEqual(q2.lead_time_days, 12)
        self.assertEqual(q2.label, "SIMULATED")

    def test_quotes_preserve_provenance(self):
        """Rule: Quotes must preserve source provenance and internal fields."""
        quotes = self.collector.load_quotes()
        for q in quotes:
            self.assertEqual(q.label, "SIMULATED")
            self.assertEqual(q.source, "SIMULATED_DATASET_STEP_5B")
            self.assertIn("headcount_total_internal", q._internal)

    def test_quote_rejects_missing_display_label(self):
        """Rule: Quotes without display labels must fail validation."""
        with self.assertRaises(QuoteValidationError):
            Quote(display_label="", unit_price=42.0, lead_time_days=10)

    def test_quote_rejects_non_simulated_label(self):
        """Rule: Every quote must be explicitly labeled SIMULATED."""
        with self.assertRaises(QuoteValidationError) as ctx:
            Quote(display_label="Supplier 1", unit_price=42.0, lead_time_days=10, label="OFFICIAL_BID")
        self.assertIn("explicitly 'SIMULATED'", str(ctx.exception))

    def test_quote_rejects_negative_or_zero_price(self):
        """Rule: Quotes with non-positive unit_price must fail validation."""
        with self.assertRaises(QuoteValidationError):
            Quote(display_label="Supplier 1", unit_price=-10.0, lead_time_days=10)
        with self.assertRaises(QuoteValidationError):
            Quote(display_label="Supplier 1", unit_price=0.0, lead_time_days=10)

    def test_quote_rejects_negative_lead_time(self):
        """Rule: Quotes with negative lead time must fail validation."""
        with self.assertRaises(QuoteValidationError):
            Quote(display_label="Supplier 1", unit_price=42.0, lead_time_days=-5)

    def test_to_contract_dict_matches_frozen_schema(self):
        """Rule: Output matches Person 1 frozen contract: {display_label, unit_price, lead_time_days, label}."""
        q = Quote(display_label="Supplier 1", unit_price=42.0, lead_time_days=10)
        contract = q.to_contract_dict()
        self.assertEqual(contract, {
            "display_label": "Supplier 1",
            "unit_price": 42.0,
            "lead_time_days": 10,
            "label": "SIMULATED"
        })


if __name__ == "__main__":
    unittest.main()

