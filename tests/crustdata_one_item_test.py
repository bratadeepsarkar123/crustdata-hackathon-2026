"""Tests for one-item supplier discovery and Option C verification (Task 1 & Task 2)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from unittest.mock import MagicMock, patch

from src.crustdata.client import CrustdataClient
from src.crustdata.exceptions import CrustdataAPIError, CrustdataCreditsExhaustedError
from src.discovery.option_c_run import (
    build_one_item_request,
    run_one_item_discovery,
    to_shortlist_payload,
)
from src.discovery.service import format_screen_display


class TestOneItemDiscovery(unittest.TestCase):

    def setUp(self):
        self.item = "neodymium speaker magnet"
        self.quantity = 1000
        self.unit = "pcs"
        self.spec = "3 mm thick, low minimum order"
        self.buyer_location = "US"
        self.supplier_region = "China"
        self.moq = "very small"

    def test_build_one_item_request_shape(self):
        req = build_one_item_request(
            item=self.item,
            quantity=self.quantity,
            unit=self.unit,
            spec=self.spec,
            buyer_location=self.buyer_location,
            supplier_region=self.supplier_region,
            moq=self.moq,
        )
        self.assertEqual(req["item"], "neodymium speaker magnet")
        self.assertEqual(req["quantity"], 1000)
        self.assertEqual(req["unit"], "pcs")
        self.assertEqual(req["spec"], "3 mm thick, low minimum order")
        self.assertEqual(req["region"], "China")
        self.assertEqual(req["buyer_location"], "US")
        self.assertEqual(req["moq"], "very small")
        self.assertTrue(req["sole_source"])

    def test_one_item_discovery_offline_fixtures(self):
        """Offline fixture execution returns 5 verified neodymium magnet suppliers in China."""
        suppliers = run_one_item_discovery(
            item=self.item,
            quantity=self.quantity,
            unit=self.unit,
            spec=self.spec,
            buyer_location=self.buyer_location,
            supplier_region=self.supplier_region,
            moq=self.moq,
            live=False,
        )
        self.assertEqual(len(suppliers), 5)

        for idx, s in enumerate(suppliers, start=1):
            self.assertEqual(s["display_label"], f"Supplier {idx}")
            self.assertEqual(s["product_line_status"], "CONFIRMED")
            self.assertGreater(s["confidence"], 0.8)
            # Verify citations contain identify and enrich endpoints
            endpoints = {src["endpoint"] for src in s.get("sources", [])}
            self.assertIn("POST /company/identify", endpoints)
            self.assertIn("POST /company/enrich", endpoints)

    def test_no_company_name_in_screen_output(self):
        """Strict Option C check: no internal company names or domains leak to the screen."""
        suppliers = run_one_item_discovery(
            item=self.item,
            quantity=self.quantity,
            unit=self.unit,
            spec=self.spec,
            buyer_location=self.buyer_location,
            supplier_region=self.supplier_region,
            moq=self.moq,
            live=False,
        )
        screen_output = format_screen_display(suppliers, is_simulated=True)

        for s in suppliers:
            name_internal = s.get("name_internal")
            domain_internal = s.get("primary_domain")
            hq_internal = s.get("headquarters_internal")
            hc_internal = str(s.get("headcount_total_internal"))

            self.assertTrue(name_internal, "Expected name_internal to exist in internal record")
            self.assertNotIn(
                name_internal.lower(),
                screen_output.lower(),
                f"Security violation: Company name '{name_internal}' leaked to screen display!",
            )
            self.assertNotIn(
                domain_internal.lower(),
                screen_output.lower(),
                f"Security violation: Domain '{domain_internal}' leaked to screen display!",
            )
            # No raw domain URLs in screen output
            self.assertNotIn(".example", screen_output.lower())
            self.assertNotIn("http://", screen_output.lower())
            self.assertNotIn("https://", screen_output.lower())

    def test_cli_option_c_run_execution(self):
        """Run CLI option_c_run.py script directly and verify exit code and stdout."""
        cmd = [sys.executable, "src/discovery/option_c_run.py"]
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
        self.assertEqual(proc.returncode, 0, f"CLI exited with error: {proc.stderr}")

        stdout = proc.stdout
        self.assertIn("[Supplier 1]", stdout)
        self.assertIn("Option C", stdout)
        self.assertIn("SIMULATED fixture", stdout)
        self.assertIn("Source: Crustdata", stdout)

        # Confirm no company names appear in CLI stdout
        forbidden_substrings = [
            "Shandong Sinter",
            "Ningbo Small",
            "Beijing Rare Earth",
            "Hangzhou Large",
            "Zhejiang NdFeB",
            ".example",
            "http://",
        ]
        for sub in forbidden_substrings:
            self.assertNotIn(sub.lower(), stdout.lower())

    def test_cli_shortlist_json_shape(self):
        """CLI --shortlist-json produces schema matching samples/one-item/supplier-shortlist.json."""
        cmd = [sys.executable, "src/discovery/option_c_run.py", "--shortlist-json"]
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
        self.assertEqual(proc.returncode, 0, f"CLI exited with error: {proc.stderr}")

        data = json.loads(proc.stdout)
        self.assertIn("item", data)
        self.assertIn("constraints", data)
        self.assertIn("suppliers", data)
        self.assertIn("recommended_label", data)

        self.assertEqual(data["item"]["name"], "neodymium speaker magnet")
        self.assertEqual(data["item"]["thickness_mm"], 3)
        self.assertEqual(data["constraints"]["supplier_country"], "China")
        self.assertEqual(len(data["suppliers"]), 5)
        self.assertEqual(data["suppliers"][0]["label"], "Supplier 1")
        self.assertTrue(len(data["suppliers"][0]["claims"]) > 0)
        self.assertIn("citation", data["suppliers"][0]["claims"][0])

    def test_live_path_fails_closed_without_api_key(self):
        """--live must fail closed with CrustdataAPIError if no key is configured."""
        with patch.dict(os.environ, {}, clear=True):
            with patch("src.discovery.option_c_run.load_api_key_from_env", return_value=None):
                with self.assertRaises(CrustdataAPIError):
                    run_one_item_discovery(live=True)

    def test_live_path_fails_closed_when_insufficient_credits(self):
        """Live path pre-flight check halts before calling search if balance is below estimate."""
        mock_client = MagicMock(spec=CrustdataClient)
        mock_client.allow_live = True
        mock_client.get_account_credits.return_value = {"account": {"credits": 0.05}}

        with patch("src.discovery.option_c_run.load_api_key_from_env", return_value="mock_key_123"):
            with patch("src.discovery.option_c_run.CrustdataClient", return_value=mock_client):
                with self.assertRaises(CrustdataCreditsExhaustedError):
                    run_one_item_discovery(live=True)

        # Zero live searches made
        mock_client.company_search.assert_not_called()

    def test_live_path_mocked_success(self):
        """Mocked live run with adequate balance succeeds and completes pipeline."""
        mock_client = MagicMock(spec=CrustdataClient)
        mock_client.allow_live = True
        mock_client.get_account_credits.return_value = {"account": {"credits": 500.0}}
        mock_client.company_search.return_value = {
            "results": [
                {
                    "name": "Live NdFeB Corp",
                    "domain": "live-ndfeb.com",
                    "year_founded": 2012,
                    "location": "Ningbo, China",
                    "relevance_score": 0.96,
                }
            ]
        }
        mock_client.company_identify.return_value = [{"crustdata_company_id": 998877}]
        mock_client.company_enrich.return_value = {
            "headcount": {"total": 120},
            "locations": {"headquarters": "Ningbo, China"},
            "basic_info": {"description": "Manufacturer of precision neodymium magnets"},
        }

        with patch("src.discovery.option_c_run.load_api_key_from_env", return_value="mock_key_123"):
            with patch("src.discovery.option_c_run.CrustdataClient", return_value=mock_client):
                suppliers = run_one_item_discovery(live=True)

        self.assertEqual(len(suppliers), 1)
        self.assertEqual(suppliers[0]["display_label"], "Supplier 1")
        self.assertEqual(suppliers[0]["product_line_status"], "CONFIRMED")
        mock_client.company_search.assert_called_once()
        mock_client.company_identify.assert_called_once()
        mock_client.company_enrich.assert_called_once()


if __name__ == "__main__":
    unittest.main()
