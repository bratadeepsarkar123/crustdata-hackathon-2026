"""Tests for Crustdata Verification (Step 3): identify first, enrich, product line check."""

import unittest
from unittest.mock import MagicMock

from src.crustdata.client import CrustdataClient
from src.crustdata.credits import CreditGuard
from src.crustdata.exceptions import (
    CrustdataBudgetExceededError,
    CrustdataCreditsExhaustedError,
    CrustdataPlanGatedError,
    CrustdataRateLimitError,
)
from src.discovery.verify import verify_supplier, verify_all_candidates


class TestCrustdataVerification(unittest.TestCase):

    def test_verify_supplier_fixture_confirmed(self):
        candidate = {
            "name_internal": "Alpha Thermal",
            "primary_domain": "alpha-thermal.example",
            "headquarters_internal": "City A, India",
            "headcount_total_internal": None,
            "product_line_status": "HUMAN_OR_SIMULATED",
            "sources": [{"field": "primary_domain", "endpoint": "/company/search"}],
            "confidence": 0.90,
        }
        verified = verify_supplier(candidate, use_fixtures=True)

        self.assertEqual(verified["headcount_total_internal"], 650)
        self.assertEqual(verified["product_line_status"], "CONFIRMED")
        self.assertGreaterEqual(verified["confidence"], 0.95)

        # Check citations
        endpoints = [s["endpoint"] for s in verified["sources"]]
        self.assertIn("POST /company/enrich", endpoints)
        fields = [s["field"] for s in verified["sources"]]
        self.assertIn("headcount.total", fields)
        self.assertIn("locations.headquarters", fields)
        self.assertIn("basic_info.description", fields)

    def test_verify_supplier_fixture_empty_description_human_or_simulated(self):
        """Empty basic_info.description must mark product_line_status as HUMAN_OR_SIMULATED."""
        candidate = {
            "name_internal": "Echo Instruments",
            "primary_domain": "echo-instruments.example",
            "headquarters_internal": "Ahmedabad, India",
            "headcount_total_internal": None,
            "product_line_status": "CONFIRMED",  # Deliberately set to test overwrite
            "sources": [],
            "confidence": 0.85,
        }
        verified = verify_supplier(candidate, use_fixtures=True)

        self.assertEqual(verified["headcount_total_internal"], 45)
        # MUST be marked HUMAN_OR_SIMULATED because description was empty in fixture
        self.assertEqual(verified["product_line_status"], "HUMAN_OR_SIMULATED")

    def test_live_verify_identify_then_enrich(self):
        """Assert identify is called first, never requesting headcount, then enrich is called."""
        mock_client = MagicMock(spec=CrustdataClient)
        mock_client.allow_live = True

        mock_client.company_identify.return_value = {
            "crustdata_company_id": 555123,
            "name": "Live Verify Co",
            "domain": "liveverify.com",
        }
        mock_client.company_enrich.return_value = {
            "crustdata_company_id": 555123,
            "headcount": {"total": 210},
            "locations": {"headquarters": "New Delhi, India"},
            "basic_info": {"description": "Manufacturer of precision thermocouples and temperature gauges."},
        }

        candidate = {
            "name_internal": "Live Verify Co",
            "primary_domain": "liveverify.com",
            "sources": [],
            "confidence": 0.80,
        }

        verified = verify_supplier(candidate, client=mock_client, use_fixtures=False)

        # 1. Identify called with name / domain, NO headcount or locations
        mock_client.company_identify.assert_called_once_with(
            names=["Live Verify Co"],
            domains=["liveverify.com"],
        )

        # 2. Enrich called by company_id for headcount, locations, basic_info
        mock_client.company_enrich.assert_called_once_with(
            company_id=555123,
            fields=["headcount", "locations", "basic_info"],
        )

        self.assertEqual(verified["headcount_total_internal"], 210)
        self.assertEqual(verified["headquarters_internal"], "New Delhi, India")
        self.assertEqual(verified["product_line_status"], "CONFIRMED")

    def test_verify_all_stops_immediately_on_402_called_only_once(self):
        """A 402 error must re-raise immediately, terminating the loop after 1 identify call."""
        mock_client = MagicMock(spec=CrustdataClient)
        mock_client.allow_live = True
        mock_client.company_identify.side_effect = CrustdataCreditsExhaustedError("HTTP 402: Credits exhausted")

        candidates = [
            {"name_internal": "Candidate 1", "primary_domain": "cand1.com"},
            {"name_internal": "Candidate 2", "primary_domain": "cand2.com"},
            {"name_internal": "Candidate 3", "primary_domain": "cand3.com"},
        ]

        with self.assertRaises(CrustdataCreditsExhaustedError):
            verify_all_candidates(candidates, client=mock_client, use_fixtures=False)

        # Assert identify was called only ONCE and did NOT continue looping
        self.assertEqual(mock_client.company_identify.call_count, 1)

    def test_verify_all_stops_immediately_on_403(self):
        """A 403 plan-gated error on enrich must stop the whole run immediately."""
        mock_client = MagicMock(spec=CrustdataClient)
        mock_client.allow_live = True
        mock_client.company_identify.return_value = {"crustdata_company_id": 101}
        mock_client.company_enrich.side_effect = CrustdataPlanGatedError("HTTP 403: Plan gated")

        candidates = [
            {"name_internal": "Candidate 1", "primary_domain": "cand1.com"},
            {"name_internal": "Candidate 2", "primary_domain": "cand2.com"},
        ]

        with self.assertRaises(CrustdataPlanGatedError):
            verify_all_candidates(candidates, client=mock_client, use_fixtures=False)

        # First candidate identified, then enrich raised 403, candidate 2 was never processed
        self.assertEqual(mock_client.company_identify.call_count, 1)
        self.assertEqual(mock_client.company_enrich.call_count, 1)

    def test_verify_all_stops_at_budget_with_100_candidates(self):
        """Must record usage after each identify/enrich call and stop when budget is reached."""
        mock_client = MagicMock(spec=CrustdataClient)
        mock_client.allow_live = True
        mock_client.company_identify.return_value = {"crustdata_company_id": 999}
        mock_client.company_enrich.return_value = {
            "headcount": {"total": 50},
            "locations": {"headquarters": "City, Country"},
            "basic_info": {"description": "Sensors"},
        }

        # 100 candidate suppliers
        candidates = [
            {"name_internal": f"Candidate {i}", "primary_domain": f"cand{i}.com"}
            for i in range(1, 101)
        ]

        # Budget of 10.0 credits: each enrich costs 2.0 credits, so 5 enriches max allowed
        guard = CreditGuard(max_budget=10.0)

        with self.assertRaises(CrustdataBudgetExceededError):
            verify_all_candidates(
                candidates=candidates,
                client=mock_client,
                use_fixtures=False,
                credit_guard=guard,
            )

        # Assert execution stopped exactly at the budget limit (5 enriches = 10.0 credits)
        self.assertEqual(mock_client.company_enrich.call_count, 5)
        self.assertEqual(guard.total_credits_used, 10.0)


if __name__ == "__main__":
    unittest.main()
