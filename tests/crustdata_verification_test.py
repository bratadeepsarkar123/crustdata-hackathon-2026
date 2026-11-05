"""Tests for Crustdata Verification (Step 3): identify first, enrich, product line check."""

import unittest
from unittest.mock import MagicMock

from src.crustdata.client import CrustdataClient
from src.discovery.verify import verify_supplier, verify_all_candidates


class TestCrustdataVerification(unittest.TestCase):

    def test_verify_supplier_fixture_confirmed(self):
        candidate = {
            "name_internal": "Tempsens Instruments",
            "primary_domain": "tempsens.com",
            "headquarters_internal": "Udaipur, India",
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
        self.assertIn("/company/enrich", endpoints)
        fields = [s["field"] for s in verified["sources"]]
        self.assertIn("headcount", fields)
        self.assertIn("locations", fields)
        self.assertIn("basic_info.description", fields)

    def test_verify_supplier_fixture_empty_description_human_or_simulated(self):
        """Empty basic_info.description must mark product_line_status as HUMAN_OR_SIMULATED."""
        candidate = {
            "name_internal": "Sensorcon Instruments",
            "primary_domain": "sensorcon-instruments.in",
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


if __name__ == "__main__":
    unittest.main()
