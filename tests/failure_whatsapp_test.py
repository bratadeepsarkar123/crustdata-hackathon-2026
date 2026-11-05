import os
import unittest
from unittest.mock import patch, MagicMock
from io import BytesIO
from src.whatsapp.config import (
    WhatsAppConfig,
    WhatsAppMode,
    WhatsAppSecurityError,
    WhatsAppConfigError,
    WhatsAppAPIError
)
from src.whatsapp.sender import WhatsAppSender
from src.whatsapp.client import MetaWhatsAppCloudClient


class TestWhatsAppGuardsAndFailures(unittest.TestCase):
    """Failure and safety test suite for WhatsApp integration (Step 5a / AC-1)."""

    def setUp(self):
        # Ensure clean environment for each test
        if "WHATSAPP_MODE" in os.environ:
            del os.environ["WHATSAPP_MODE"]

    def test_default_mode_is_simulated(self):
        """Rule: WhatsApp mode must strictly default to SIMULATED."""
        config = WhatsAppConfig()
        self.assertEqual(config.mode, WhatsAppMode.SIMULATED)

    def test_invalid_mode_rejected(self):
        """Rule: Any mode other than SIMULATED or TEAM_PHONE must raise WhatsAppSecurityError."""
        with self.assertRaises(WhatsAppSecurityError) as ctx:
            WhatsAppConfig(mode="LIVE_PRODUCTION")
        self.assertIn("Invalid WhatsApp mode", str(ctx.exception))

    def test_team_phone_mode_allows_approved_numbers(self):
        """Rule: In TEAM_PHONE mode, explicitly approved team numbers must be allowed."""
        config = WhatsAppConfig(
            mode="TEAM_PHONE",
            allowlist={"+919876543210", "+919876543211"}
        )
        self.assertTrue(config.validate_destination("+919876543210", is_supplier=False))
        self.assertTrue(config.validate_destination("+919876543211", is_supplier=False))

    def test_team_phone_mode_rejects_unapproved_numbers(self):
        """Rule: In TEAM_PHONE mode, any non-allowlisted number must be blocked."""
        config = WhatsAppConfig(
            mode="TEAM_PHONE",
            allowlist={"+919876543210"}
        )
        with self.assertRaises(WhatsAppSecurityError) as ctx:
            config.validate_destination("+14155552671", is_supplier=False)
        self.assertIn("not in the approved team allowlist", str(ctx.exception))

    def test_supplier_outreach_strictly_prohibited_in_live_mode(self):
        """Rule: Never contact real suppliers over cellular networks."""
        config = WhatsAppConfig(
            mode="TEAM_PHONE",
            allowlist={"+919876543210"}
        )
        sender = WhatsAppSender(config=config)
        with self.assertRaises(WhatsAppSecurityError) as ctx:
            sender.send_rfq_request(
                display_label="Supplier 1",
                phone="+919876543210",
                item_description="Industrial Sensors",
                quantity=500,
                idempotency_key="key-sup-test",
                is_supplier=True
            )
        self.assertIn("supplier contact is strictly SIMULATED", str(ctx.exception))

    def test_simulated_mode_safe_dispatch(self):
        """Rule: In SIMULATED mode, RFQs are logged with 'SIMULATED' label and not dispatched externally."""
        config = WhatsAppConfig(mode="SIMULATED")
        sender = WhatsAppSender(config=config)
        msg = sender.send_rfq_request(
            display_label="Supplier 1",
            phone="+919999999999",
            item_description="Industrial Sensors",
            quantity=500,
            idempotency_key="rfq-sup1-sim",
            is_supplier=True
        )
        self.assertEqual(msg["label"], "SIMULATED")
        self.assertEqual(msg["mode"], "SIMULATED")
        self.assertEqual(msg["display_label"], "Supplier 1")
        self.assertEqual(msg["destination_phone"], "SIMULATED_CHANNEL")

    def test_no_secrets_in_logs_or_messages(self):
        """Rule: WhatsApp tokens/secrets must never appear in message records or logs."""
        config = WhatsAppConfig(mode="SIMULATED")
        sender = WhatsAppSender(config=config)
        msg = sender.send_rfq_request(
            display_label="Supplier 1",
            phone="+919876543210",
            item_description="Sensors",
            quantity=500,
            idempotency_key="msg-1"
        )
        for key in ["token", "secret", "api_key", "password"]:
            self.assertNotIn(key, msg)

    def test_meta_client_raises_when_credentials_missing(self):
        """Rule: Attempting to call Meta Cloud API without credentials raises WhatsAppConfigError."""
        config = WhatsAppConfig(mode="TEAM_PHONE", allowlist={"+919876543210"})
        # Ensure credentials empty
        config.access_token = ""
        config.phone_number_id = ""
        client = MetaWhatsAppCloudClient(config=config)
        with self.assertRaises(WhatsAppConfigError) as ctx:
            client.send_text_message("+919876543210", "Hello team")
        self.assertIn("Missing Meta Cloud API credentials", str(ctx.exception))

    @patch("urllib.request.urlopen")
    def test_meta_client_successful_mocked_dispatch(self, mock_urlopen):
        """Rule: Meta Cloud API client formats payload and returns response upon HTTP 200."""
        config = WhatsAppConfig(mode="TEAM_PHONE", allowlist={"+919876543210"})
        config.access_token = "mock_token_123"
        config.phone_number_id = "phone_id_999"

        # Mock HTTP response
        mock_response = MagicMock()
        mock_response.read.return_value = b'{"messaging_product": "whatsapp", "messages": [{"id": "wamid.test12345"}]}'
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        client = MetaWhatsAppCloudClient(config=config)
        resp = client.send_text_message("+919876543210", "Test notification")
        self.assertEqual(resp["messaging_product"], "whatsapp")
        self.assertEqual(resp["messages"][0]["id"], "wamid.test12345")
        # Ensure urlopen called
        self.assertTrue(mock_urlopen.called)

    @patch("urllib.request.urlopen")
    def test_team_message_idempotent_with_meta_client(self, mock_urlopen):
        """Rule: In TEAM_PHONE mode, repeated team notifications execute Meta Cloud API once."""
        config = WhatsAppConfig(mode="TEAM_PHONE", allowlist={"+919876543210"})
        config.access_token = "mock_token_123"
        config.phone_number_id = "phone_id_999"

        mock_response = MagicMock()
        mock_response.read.return_value = b'{"messages": [{"id": "wamid.test999"}]}'
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        sender = WhatsAppSender(config=config)
        key = "team-notif-key-01"

        # 1st send calls API
        r1 = sender.send_team_message(
            phone="+919876543210",
            text="Please review exception",
            idempotency_key=key
        )
        self.assertEqual(mock_urlopen.call_count, 1)
        self.assertFalse(r1["reused_cached_result"])

        # 2nd send with same key does not call API again
        r2 = sender.send_team_message(
            phone="+919876543210",
            text="Please review exception",
            idempotency_key=key
        )
        self.assertEqual(mock_urlopen.call_count, 1)  # Still 1!
        self.assertTrue(r2["reused_cached_result"])

    def test_to_contract_message_matches_frozen_keys(self):
        """Rule: WhatsApp message contract matches Person 1 frozen contract keys exactly."""
        sender = WhatsAppSender(config=WhatsAppConfig(mode="SIMULATED"))
        msg = sender.send_rfq_request(
            display_label="Supplier 1",
            phone="+919876543210",
            item_description="Sensors",
            quantity=500,
            idempotency_key="key-exact-keys"
        )
        contract_msg = WhatsAppSender.to_contract_message(msg)
        expected_keys = {"display_label", "direction", "text", "idempotency_key", "mode", "label"}
        self.assertEqual(set(contract_msg.keys()), expected_keys)
        self.assertEqual(contract_msg["label"], "SIMULATED")


if __name__ == "__main__":
    unittest.main()

