import unittest
from src.quotes.models import Quote
from src.policy.models import ProcurementPolicy
from src.policy.evaluator import PolicyEvaluator


class TestPolicyComparisonAndFailures(unittest.TestCase):
    """Failure, budget threshold, and exceptions queue tests (Step 6 / AC-3)."""

    def setUp(self):
        # 500 sensors, budget $25,000, deadline 14 days, min headcount 10
        self.policy = ProcurementPolicy(
            budget_ceiling_usd=25000.0,
            required_delivery_days=14,
            min_vendor_headcount=10,
            allowed_payment_terms=["Net 30", "Net 45"]
        )
        self.evaluator = PolicyEvaluator(policy=self.policy)

    def test_supplier_1_under_budget_passes(self):
        """Rule: Supplier 1 ($21,000 <= $25,000) passes budget and policy evaluation."""
        q1 = Quote(
            display_label="Supplier 1",
            unit_price=42.0,
            quantity=500,
            lead_time_days=10,
            payment_terms="Net 30",
            _internal={"headcount_total_internal": 58}
        )
        result = self.evaluator.evaluate_quote(q1)
        self.assertTrue(result.is_compliant)
        self.assertIsNone(result.exception_reason)
        self.assertEqual(result.total_price, 21000.0)
        self.assertEqual(self.evaluator.exceptions_queue.count(), 0)

    def test_supplier_2_over_budget_enters_exceptions_queue(self):
        """Rule: Supplier 2 ($27,500 > $25,000) MUST enter exceptions queue with OVER_BUDGET reason."""
        q2 = Quote(
            display_label="Supplier 2",
            unit_price=55.0,
            quantity=500,
            lead_time_days=12,
            payment_terms="Net 30",
            _internal={"headcount_total_internal": 28}
        )
        result = self.evaluator.evaluate_quote(q2)
        self.assertFalse(result.is_compliant)
        self.assertIsNotNone(result.exception_reason)
        self.assertIn("OVER_BUDGET", result.exception_reason)
        self.assertIn("$27,500.00 exceeds budget ceiling $25,000.00", result.exception_reason)
        
        # Verify in exceptions queue
        self.assertEqual(self.evaluator.exceptions_queue.count(), 1)
        record = self.evaluator.exceptions_queue.get_records()[0]
        self.assertEqual(record.display_label, "Supplier 2")
        self.assertEqual(record.status, "EXCEPTION")
        self.assertEqual(record.label, "SIMULATED")
        self.assertIn("OVER_BUDGET", record.reason)

    def test_lead_time_exceeded_enters_exceptions_queue(self):
        """Rule: Quote exceeding delivery deadline (16 > 14 days) enters exceptions queue."""
        q_late = Quote(
            display_label="Supplier 3",
            unit_price=40.0,
            quantity=500,
            lead_time_days=16,
            _internal={"headcount_total_internal": 30}
        )
        result = self.evaluator.evaluate_quote(q_late)
        self.assertFalse(result.is_compliant)
        self.assertIn("LEAD_TIME_EXCEEDED", result.exception_reason)
        self.assertEqual(self.evaluator.exceptions_queue.count(), 1)

    def test_insufficient_headcount_enters_exceptions_queue(self):
        """Rule: Quote with vendor headcount below policy minimum (< 10) enters exceptions queue."""
        q_small = Quote(
            display_label="Supplier 4",
            unit_price=41.0,
            quantity=500,
            lead_time_days=10,
            _internal={"headcount_total_internal": 4}
        )
        result = self.evaluator.evaluate_quote(q_small)
        self.assertFalse(result.is_compliant)
        self.assertIn("INSUFFICIENT_HEADCOUNT", result.exception_reason)

    def test_ranking_and_exceptions_separation(self):
        """Rule: evaluate_all ranks compliant quotes and isolates non-compliant ones into exceptions queue."""
        q1 = Quote(display_label="Supplier 1", unit_price=42.0, quantity=500, lead_time_days=10)
        q2 = Quote(display_label="Supplier 2", unit_price=55.0, quantity=500, lead_time_days=12)
        q3 = Quote(display_label="Supplier 3", unit_price=45.0, quantity=500, lead_time_days=8)

        results, exceptions = self.evaluator.evaluate_all([q1, q2, q3])
        self.assertEqual(len(results), 3)
        self.assertEqual(exceptions.count(), 1)  # Only Supplier 2 is over budget

        # Check ranking among compliant
        # q1 ($21k) vs q3 ($22.5k) -> q1 rank 1, q3 rank 2
        r1 = next(r for r in results if r.display_label == "Supplier 1")
        r3 = next(r for r in results if r.display_label == "Supplier 3")
        self.assertEqual(r1.rank, 1)
        self.assertEqual(r3.rank, 2)

    def test_integration_with_person_2_supplier_object(self):
        """Rule: Policy evaluator seamlessly reads headcount_total_internal from Person 2 candidate supplier."""
        candidate_supplier = {
            "display_label": "Supplier 1",
            "name_internal": "Apex Sensor Systems Inc.",
            "primary_domain": "apexsensors.com",
            "headcount_total_internal": 58,
            "product_line_status": "CONFIRMED"
        }
        quote = Quote(display_label="Supplier 1", unit_price=42.0, quantity=500, lead_time_days=10)
        result = self.evaluator.evaluate_quote(quote, supplier=candidate_supplier)
        self.assertTrue(result.is_compliant)
        self.assertIn("58 >= 10", result.checks.get("headcount_check", ""))

    def test_to_contract_decision_matches_frozen_keys(self):
        """Rule: Policy decision output matches Person 1 frozen contract keys: {label, approved, display_label, reason}."""
        q1 = Quote(display_label="Supplier 1", unit_price=42.0, quantity=500, lead_time_days=10)
        result = self.evaluator.evaluate_quote(q1)
        contract_decision = result.to_contract_decision()
        expected_keys = {"label", "approved", "display_label", "reason"}
        self.assertEqual(set(contract_decision.keys()), expected_keys)
        self.assertTrue(contract_decision["approved"])
        self.assertEqual(contract_decision["display_label"], "Supplier 1")
        self.assertEqual(contract_decision["label"], "SIMULATED")


if __name__ == "__main__":
    unittest.main()

