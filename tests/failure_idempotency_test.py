import unittest
from src.whatsapp.sender import WhatsAppSender
from src.whatsapp.config import WhatsAppConfig
from src.policy.retry_guard import (
    IdempotencyStore,
    ActionRetryGuard,
    PORetryGuard,
    IdempotencyError
)


class TestIdempotencyAndPORetries(unittest.TestCase):
    """Idempotency, duplicate prevention, and retry semantics test suite (AC-4 / Step 7)."""

    def setUp(self):
        self.store = IdempotencyStore()

    def test_whatsapp_repeated_send_executes_once(self):
        """Rule: A repeated WhatsApp send with the same idempotency key sends once."""
        sender = WhatsAppSender(config=WhatsAppConfig(mode="SIMULATED"))
        key = "idemp-wa-rfq-001"

        # First call
        res1 = sender.send_rfq_request(
            display_label="Supplier 1",
            phone="+919876543210",
            item_description="Industrial Sensors",
            quantity=500,
            idempotency_key=key
        )
        self.assertFalse(res1["reused_cached_result"])
        self.assertEqual(len(sender.get_message_log()), 1)

        # Second call with same key
        res2 = sender.send_rfq_request(
            display_label="Supplier 1",
            phone="+919876543210",
            item_description="Industrial Sensors",
            quantity=500,
            idempotency_key=key
        )
        self.assertTrue(res2["reused_cached_result"])
        # Log should still have only 1 send
        self.assertEqual(len(sender.get_message_log()), 1)
        self.assertEqual(res1["timestamp"], res2["timestamp"])

    def test_po_retry_guard_prevents_duplicate_po_writes(self):
        """Rule: A repeated PO write with the same key executes once and reuses the previous PO."""
        guard = PORetryGuard(store=self.store)
        po_execution_counter = {"count": 0}

        def mock_person_1_po_create(idempotency_key, display_label, total, po_number=None):
            po_execution_counter["count"] += 1
            return {
                "idempotency_key": idempotency_key,
                "display_label": display_label,
                "po_number": po_number or f"PO-2026-{po_execution_counter['count']:04d}-SIMULATED",
                "total": total,
                "status": "APPROVED",
                "label": "SIMULATED"
            }

        key = "VEND-ONBOARD-a7f4e92b3c1d"

        # First PO call
        po1 = guard.create_po_idempotent(
            po_creation_fn=mock_person_1_po_create,
            idempotency_key=key,
            display_label="Supplier 1",
            total=21000.0
        )
        self.assertEqual(po_execution_counter["count"], 1)
        self.assertEqual(po1["po_number"], "PO-2026-0001-SIMULATED")

        # Second PO call with same key
        po2 = guard.create_po_idempotent(
            po_creation_fn=mock_person_1_po_create,
            idempotency_key=key,
            display_label="Supplier 1",
            total=21000.0
        )
        # Function was NOT called a second time
        self.assertEqual(po_execution_counter["count"], 1)
        self.assertEqual(po2["po_number"], "PO-2026-0001-SIMULATED")
        self.assertTrue(po2.get("idempotency_replayed", False))

    def test_retry_after_transient_failure_succeeds(self):
        """Rule: If an action encounters a transient failure, it safely retries on the next call."""
        guard = ActionRetryGuard(store=self.store)
        attempts = {"count": 0}

        def flaky_action():
            attempts["count"] += 1
            if attempts["count"] == 1:
                raise ConnectionError("Transient network glitch (HTTP 503)")
            return {"status": "SUCCESS", "data": "processed"}

        key = "flaky-action-key"

        # First attempt fails
        with self.assertRaises(ConnectionError):
            guard.execute(key, flaky_action, max_retries=3)

        stored_state = self.store.get(key)
        self.assertEqual(stored_state["status"], "FAILED")
        self.assertEqual(stored_state["attempts"], 2)

        # Second attempt succeeds
        result = guard.execute(key, flaky_action, max_retries=3)
        self.assertEqual(result["status"], "SUCCESS")
        self.assertEqual(self.store.get(key)["status"], "SUCCESS")
        self.assertEqual(attempts["count"], 2)

        # Third attempt reuses success without re-calling
        cached = guard.execute(key, flaky_action, max_retries=3)
        self.assertEqual(attempts["count"], 2)  # Not called again

    def test_max_retries_exceeded_raises_error(self):
        """Rule: Exceeding maximum retries raises IdempotencyError."""
        guard = ActionRetryGuard(store=self.store)

        def failing_action():
            raise RuntimeError("Permanent downstream failure")

        key = "permanent-fail-key"

        # Attempts 1 and 2 fail
        with self.assertRaises(RuntimeError):
            guard.execute(key, failing_action, max_retries=2)

        # Exceeds max retries
        with self.assertRaises(IdempotencyError) as ctx:
            guard.execute(key, failing_action, max_retries=2)
        self.assertIn("exceeded maximum retries", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()

