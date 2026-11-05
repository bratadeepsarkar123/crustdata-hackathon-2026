import unittest
from src.whatsapp.sender import WhatsAppSender
from src.whatsapp.config import WhatsAppConfig
from src.quotes.collector import QuoteCollector
from src.policy.models import ProcurementPolicy
from src.policy.evaluator import PolicyEvaluator
from src.policy.retry_guard import PORetryGuard, IdempotencyStore


class TestEndToEndDemoScenario(unittest.TestCase):
    """End-to-end acceptance verification of the exact hackathon demo scenario (Phase 4)."""

    def setUp(self):
        self.policy = ProcurementPolicy(
            budget_ceiling_usd=25000.0,
            required_delivery_days=14,
            min_vendor_headcount=10
        )
        self.quote_collector = QuoteCollector()
        self.evaluator = PolicyEvaluator(policy=self.policy)
        self.whatsapp_sender = WhatsAppSender(config=WhatsAppConfig(mode="SIMULATED"))
        self.po_guard = PORetryGuard(store=IdempotencyStore())

    def test_complete_demo_procurement_scenario(self):
        # 1. Person 2 discovery output (candidate verified suppliers)
        person_2_candidates = [
            {
                "display_label": "Supplier 1",
                "name_internal": "Apex Sensor Systems Inc.",
                "primary_domain": "apexsensors.com",
                "headcount_total_internal": 58,
                "product_line_status": "CONFIRMED",
                "sources": [{"field": "headcount.total", "endpoint": "POST /company/enrich"}]
            },
            {
                "display_label": "Supplier 2",
                "name_internal": "Precision Transducers Ltd.",
                "primary_domain": "precisiontransducers.co.in",
                "headcount_total_internal": 28,
                "product_line_status": "CONFIRMED",
                "sources": [{"field": "headcount.total", "endpoint": "POST /company/enrich"}]
            }
        ]

        # 2. Step 5a: Dispatch RFQ via WhatsApp (SIMULATED mode)
        wa_record_1 = self.whatsapp_sender.send_rfq_request(
            supplier=person_2_candidates[0],
            item_description="500 Industrial Temperature Sensors",
            quantity=500,
            idempotency_key="rfq-wa-supplier-1"
        )
        wa_record_2 = self.whatsapp_sender.send_rfq_request(
            supplier=person_2_candidates[1],
            item_description="500 Industrial Temperature Sensors",
            quantity=500,
            idempotency_key="rfq-wa-supplier-2"
        )
        self.assertEqual(wa_record_1["label"], "SIMULATED")
        self.assertEqual(wa_record_2["label"], "SIMULATED")
        self.assertEqual(len(self.whatsapp_sender.get_message_log()), 2)

        # 3. Step 5b: Collect simulated quotes
        quotes = self.quote_collector.load_quotes()
        self.assertEqual(len(quotes), 2)
        q1 = quotes[0]
        q2 = quotes[1]

        # Validate deterministic figures
        self.assertEqual(q1.display_label, "Supplier 1")
        self.assertEqual(q1.unit_price, 42.0)
        self.assertEqual(q1.total_price, 21000.0)
        self.assertEqual(q1.lead_time_days, 10)
        self.assertEqual(q1.label, "SIMULATED")

        self.assertEqual(q2.display_label, "Supplier 2")
        self.assertEqual(q2.unit_price, 55.0)
        self.assertEqual(q2.total_price, 27500.0)
        self.assertEqual(q2.lead_time_days, 12)
        self.assertEqual(q2.label, "SIMULATED")

        # 4. Step 6: Policy evaluation
        results, exceptions = self.evaluator.evaluate_all(quotes, suppliers=person_2_candidates)

        # Supplier 1 must PASS
        res1 = next(r for r in results if r.display_label == "Supplier 1")
        self.assertTrue(res1.is_compliant)
        self.assertEqual(res1.rank, 1)
        self.assertEqual(res1.total_price, 21000.0)
        self.assertIn("PASS ($21,000.00 <= $25,000.00)", res1.checks["budget_check"])

        # Supplier 2 must FAIL on budget ($27,500 > $25,000) and enter exceptions queue
        res2 = next(r for r in results if r.display_label == "Supplier 2")
        self.assertFalse(res2.is_compliant)
        self.assertIn("OVER_BUDGET", res2.exception_reason)
        self.assertIn("$27,500.00 exceeds budget ceiling $25,000.00", res2.exception_reason)

        self.assertEqual(exceptions.count(), 1)
        exc_record = exceptions.get_records()[0]
        self.assertEqual(exc_record.display_label, "Supplier 2")
        self.assertIn("OVER_BUDGET", exc_record.reason)

        # 5. Step 7: Idempotent PO creation handoff to Person 1
        po_creation_invocations = {"count": 0}

        def mock_person_1_po_create(idempotency_key, display_label, total, po_number=None):
            po_creation_invocations["count"] += 1
            return {
                "idempotency_key": idempotency_key,
                "display_label": display_label,
                "po_number": po_number or "PO-2026-9901-SIMULATED",
                "total": total,
                "status": "APPROVED",
                "label": "SIMULATED"
            }

        po_key = "VEND-ONBOARD-a7f4e92b3c1d"

        # First PO creation
        po_result_1 = self.po_guard.create_po_idempotent(
            po_creation_fn=mock_person_1_po_create,
            idempotency_key=po_key,
            display_label=res1.display_label,
            total=res1.total_price
        )
        self.assertEqual(po_creation_invocations["count"], 1)
        self.assertEqual(po_result_1["po_number"], "PO-2026-9901-SIMULATED")
        self.assertEqual(po_result_1["total"], 21000.0)
        self.assertEqual(po_result_1["label"], "SIMULATED")

        # Duplicate retry with same idempotency key
        po_result_2 = self.po_guard.create_po_idempotent(
            po_creation_fn=mock_person_1_po_create,
            idempotency_key=po_key,
            display_label=res1.display_label,
            total=res1.total_price
        )
        # Verify function was NOT called again
        self.assertEqual(po_creation_invocations["count"], 1)
        self.assertEqual(po_result_2["po_number"], "PO-2026-9901-SIMULATED")
        self.assertTrue(po_result_2.get("idempotency_replayed", False))


if __name__ == "__main__":
    unittest.main()

