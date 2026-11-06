"""Tests for Crustdata client: headers, 429 backoff, 402/403 stops, key masking."""

import os
import unittest
from unittest.mock import MagicMock, patch

from src.crustdata.client import CrustdataClient, mask_key, verify_file_git_ignored
from src.crustdata.exceptions import (
    CrustdataAPIError,
    CrustdataAuthError,
    CrustdataBudgetExceededError,
    CrustdataCreditsExhaustedError,
    CrustdataPlanGatedError,
    CrustdataRateLimitError,
)
from src.crustdata.credits import calculate_batch_cost, CreditGuard


class TestCrustdataClient(unittest.TestCase):

    def test_client_headers(self):
        client = CrustdataClient(api_key="mock_test_secret_123456789")
        headers = client._get_headers()
        self.assertEqual(headers["Authorization"], "Bearer mock_test_secret_123456789")
        self.assertEqual(headers["x-api-version"], "2025-11-01")
        self.assertEqual(headers["Content-Type"], "application/json")

    def test_client_repr_masks_key(self):
        client = CrustdataClient(api_key="mock_dummy_secret_key_987654321")
        client_repr = repr(client)
        self.assertNotIn("987654321", client_repr)
        self.assertIn("mock_dummy_secret_key_987654321"[:4], client_repr)
        self.assertIn("***", mask_key("short"))

    def test_live_calls_disabled_by_default(self):
        client = CrustdataClient(api_key="test_key", allow_live=False)
        with self.assertRaises(CrustdataAPIError) as ctx:
            client.get_account_credits()
        self.assertIn("Live Crustdata calls are disabled", str(ctx.exception))

    def test_stops_immediately_on_402(self):
        """HTTP 402 (Credits exhausted) must stop immediately with no retries."""
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 402
        mock_response.text = '{"error": "Payment Required - credits exhausted"}'
        mock_session.request.return_value = mock_response

        client = CrustdataClient(api_key="test_key", allow_live=True, session=mock_session)
        with self.assertRaises(CrustdataCreditsExhaustedError) as ctx:
            client.get_account_credits()

        self.assertIn("HTTP 402: Crustdata credits exhausted", str(ctx.exception))
        # Ensure it stopped immediately: exactly 1 request attempted, zero retries
        self.assertEqual(mock_session.request.call_count, 1)

    def test_stops_immediately_on_403(self):
        """HTTP 403 (Plan-gated) must stop immediately with no retries."""
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.text = '{"error": "Forbidden - plan gated"}'
        mock_session.request.return_value = mock_response

        client = CrustdataClient(api_key="test_key", allow_live=True, session=mock_session)
        with self.assertRaises(CrustdataPlanGatedError) as ctx:
            client.company_enrich(domain="example.com", fields=["technographics"])

        self.assertIn("HTTP 403: Endpoint or requested field", str(ctx.exception))
        # Exactly 1 request attempted, zero retries
        self.assertEqual(mock_session.request.call_count, 1)

    @patch("time.sleep", return_value=None)
    def test_client_429_backoff_and_succeeds(self, mock_sleep):
        """HTTP 429 should retry with backoff and succeed if subsequent attempt returns 200."""
        mock_session = MagicMock()
        resp_429 = MagicMock()
        resp_429.status_code = 429
        resp_429.headers = {"Retry-After": "2"}

        resp_200 = MagicMock()
        resp_200.status_code = 200
        resp_200.json.return_value = {"status": "success", "results": []}

        mock_session.request.side_effect = [resp_429, resp_200]

        client = CrustdataClient(
            api_key="test_key",
            allow_live=True,
            session=mock_session,
            backoff_base=0.1,
            max_retries=2,
        )
        res = client.company_search(query="sensors")
        self.assertEqual(res, {"status": "success", "results": []})
        self.assertEqual(mock_session.request.call_count, 2)
        mock_sleep.assert_called_once_with(2.0)

    @patch("time.sleep", return_value=None)
    def test_client_429_exhausted_retries(self, mock_sleep):
        """HTTP 429 should raise CrustdataRateLimitError when max retries exceeded."""
        mock_session = MagicMock()
        resp_429 = MagicMock()
        resp_429.status_code = 429
        resp_429.headers = {}
        mock_session.request.return_value = resp_429

        client = CrustdataClient(
            api_key="test_key",
            allow_live=True,
            session=mock_session,
            backoff_base=0.1,
            max_retries=2,
        )
        with self.assertRaises(CrustdataRateLimitError):
            client.company_search(query="sensors")

        # 1 initial + 2 retries = 3 calls
        self.assertEqual(mock_session.request.call_count, 3)

    def test_never_request_headcount_or_locations_on_identify(self):
        """Identify must reject requests for headcount or locations to avoid plan-gating 403."""
        client = CrustdataClient(api_key="test_key", allow_live=True)
        with self.assertRaises(ValueError) as ctx:
            client.company_identify(names=["Acme"], fields=["headcount"])
        self.assertIn("Never request 'headcount' or 'locations' on company/identify", str(ctx.exception))

        with self.assertRaises(ValueError):
            client.company_identify(names=["Acme"], fields=["locations"])

    def test_credit_cost_calculation(self):
        # 20 search results (0.60) + 5 identifies (free) + 5 enriches (10.0) + 1 autocomplete (free) = 10.60
        cost = calculate_batch_cost(search_results_count=20, identify_count=5, enrich_count=5, autocomplete_count=1)
        self.assertEqual(cost, 10.60)
        self.assertLess(cost, 200.0)

    def test_credit_guard_has_no_run_cap_by_default(self):
        guard = CreditGuard()
        self.assertIsNone(guard.max_budget)
        guard.estimate_and_check(5000.0)
        guard.record_usage(4500.0, "large run")
        guard.record_usage(900.0, "large run")
        self.assertEqual(guard.total_credits_used, 5400.0)

    def test_credit_guard_budget_under_200(self):
        guard = CreditGuard(max_budget=200.0)
        guard.record_usage(10.6, "batch run")
        self.assertEqual(guard.total_credits_used, 10.6)

        # Propose run that exceeds 200
        with self.assertRaises(CrustdataBudgetExceededError):
            guard.estimate_and_check(190.0)


if __name__ == "__main__":
    unittest.main()
